package main

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"strings"
	"testing"
	"time"
)

var validSpec = Spec{
	Image:      "sha256:" + strings.Repeat("ab", 32),
	Tree:       "/work/ab",
	PythonPath: []string{"src"},
	Timeout:    time.Minute,
	Args:       []string{"fourway_scenarios", "-q"},
}

// flagValues returns every value given for flag in args.
func flagValues(args []string, flag string) []string {
	var values []string
	for i, a := range args {
		if a == flag && i+1 < len(args) {
			values = append(values, args[i+1])
		}
	}
	return values
}

func TestPolicyMeetsDecision0002(t *testing.T) {
	// Each of these is a requirement of docs/decisions/0002, or of 0003's
	// reading of it. Dropping one reopens the path from a prompt-injected diff
	// to code that reaches the network, the user's secrets, or their files.
	args := dockerArgs(validSpec, "fourway-test")
	for flag, want := range map[string]string{
		"--network":      "none",
		"--pull":         "never",
		"--user":         nobody,
		"--cap-drop":     "ALL",
		"--security-opt": "no-new-privileges",
	} {
		if got := flagValues(args, flag); !slices.Equal(got, []string{want}) {
			t.Errorf("%s = %v, want [%s]", flag, got, want)
		}
	}
	if !slices.Contains(args, "--read-only") {
		t.Error("the image's filesystem is writable: a session could plant code for the next one")
	}
	if got := flagValues(args, "--mount"); !slices.Equal(got, []string{"type=bind,src=/work/ab,dst=/tree,readonly"}) {
		t.Errorf("mounts = %v, want only the tree, read-only", got)
	}
	for _, banned := range []string{"-v", "--volume", "--env-file", "--privileged", "--network=host", "-e"} {
		if slices.Contains(args, banned) {
			t.Errorf("%s gives the session host access", banned)
		}
	}
}

func TestNoHostEnvironmentReachesTheSession(t *testing.T) {
	// "--env NAME" without a value copies NAME from the caller's environment,
	// which is how an API key would leak into a scenario.
	for _, kv := range flagValues(dockerArgs(validSpec, "fourway-test"), "--env") {
		if !strings.Contains(kv, "=") {
			t.Errorf("--env %s passes the host's value through", kv)
		}
	}
}

func TestPythonPathMatchesTheLocalRunner(t *testing.T) {
	// src/fourway/runner.py puts the tree root first, then the suite's
	// directories; a different order changes which module an import finds.
	got := flagValues(dockerArgs(validSpec, "fourway-test"), "--env")
	if !slices.Contains(got, "PYTHONPATH=/tree:/tree/src") {
		t.Errorf("env = %v, want PYTHONPATH=/tree:/tree/src", got)
	}
}

func TestValidateRefusesWhatDockerWouldMisread(t *testing.T) {
	cases := map[string]func(*Spec){
		"a tag can move between runs":          func(s *Spec) { s.Image = "fourway-sandbox" },
		"a relative tree depends on the cwd":   func(s *Spec) { s.Tree = "work/ab" },
		"a comma splits the --mount option":    func(s *Spec) { s.Tree = "/work/a,dst=/etc" },
		"a parent pythonpath leaves the tree":  func(s *Spec) { s.PythonPath = []string{"../x"} },
		"an absolute pythonpath leaves it too": func(s *Spec) { s.PythonPath = []string{"/usr"} },
		"a colon splits PYTHONPATH":            func(s *Spec) { s.PythonPath = []string{"a:/usr"} },
		"no timeout never ends":                func(s *Spec) { s.Timeout = 0 },
	}
	if err := validSpec.Validate(); err != nil {
		t.Fatalf("valid spec refused: %v", err)
	}
	for why, mutate := range cases {
		s := validSpec
		s.PythonPath = slices.Clone(s.PythonPath)
		mutate(&s)
		if s.Validate() == nil {
			t.Errorf("accepted, but %s", why)
		}
	}
}

func TestParseReportTreatsSessionOutputAsUntrusted(t *testing.T) {
	good := `{"tests": {"t.py::test_x": "passed"}, "collect_errors": [], "exitstatus": 0}`
	cases := map[string]struct {
		out  string
		ok   bool
		over bool
	}{
		"a plugin report":                {good, true, false},
		"no report":                      {"", false, false},
		"a truncated report":             {good[:20], false, false},
		"two reports, one forged":        {good + good, false, false},
		"a field the plugin never wrote": {`{"tests": {}, "collect_errors": [], "verdict": "clean"}`, false, false},
		"no tests key":                   {`{"collect_errors": []}`, false, false},
		"more than fits in memory":       {good, false, true},
	}
	for name, c := range cases {
		out := &capped{limit: maxReport}
		out.WriteString(c.out)
		out.overflow = c.over
		if _, ok := parseReport(out); ok != c.ok {
			t.Errorf("%s: ok = %v, want %v", name, ok, c.ok)
		}
	}
}

func TestCappedKeepsOnlyTheLimit(t *testing.T) {
	c := &capped{limit: 4}
	if n, err := c.Write([]byte("abcdef")); n != 6 || err != nil {
		t.Fatalf("Write = %d, %v; a short write would stall the docker client", n, err)
	}
	if c.String() != "abcd" || !c.overflow {
		t.Errorf("kept %q, overflow %v", c.String(), c.overflow)
	}
}

// The tests from here on run real containers. CI sets FOURWAY_SANDBOX_IMAGE,
// so they never skip there.

func image(t *testing.T) string {
	name := os.Getenv("FOURWAY_SANDBOX_IMAGE")
	if name == "" {
		t.Skip("FOURWAY_SANDBOX_IMAGE is not set")
	}
	id, err := ResolveImage("docker", name)
	if err != nil {
		t.Fatal(err)
	}
	return id
}

var pytestArgs = []string{".", "-q", "-p", "no:cacheprovider", "-p", "fourway.pytest_plugin", "--import-mode=importlib"}

func session(t *testing.T, id string, source string, timeout time.Duration) (Result, string) {
	t.Helper()
	// t.TempDir is 0700; on Linux the container's nobody user could not read
	// it. gitops.export makes trees 0755, so match that.
	tree := t.TempDir()
	if err := os.Chmod(tree, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(tree, "test_session.py"), []byte(source), 0o644); err != nil {
		t.Fatal(err)
	}
	real, err := filepath.EvalSymlinks(tree)
	if err != nil {
		t.Fatal(err)
	}
	result, err := Run(context.Background(), "docker", Spec{Image: id, Tree: real, Timeout: timeout, Args: pytestArgs})
	if err != nil {
		t.Fatalf("sandbox failed: %v", err)
	}
	return result, real
}

// Each test asserts from inside the container that one escape route is closed.
const hostile = `
import os, pathlib, socket
import pytest

def test_no_network():
    with pytest.raises(OSError):
        socket.create_connection(("1.1.1.1", 53), timeout=3)

def test_no_dns():
    with pytest.raises(OSError):
        socket.getaddrinfo("example.com", 443)

def test_no_host_environment():
    assert "FOURWAY_CANARY" not in os.environ

def test_no_docker_socket():
    assert not os.path.exists("/var/run/docker.sock")

def test_tree_is_read_only():
    with pytest.raises(OSError):
        pathlib.Path("/tree/planted.py").write_text("x = 1\n")

def test_image_is_read_only():
    with pytest.raises(OSError):
        pathlib.Path("/usr/local/lib/python3.12/site-packages/planted.py").write_text("x = 1\n")

def test_not_root():
    assert os.getuid() == 65534

def test_tmp_path_works(tmp_path):
    (tmp_path / "f").write_text("scenarios use tmp_path")
`

func TestASessionCannotReachTheHost(t *testing.T) {
	id := image(t)
	t.Setenv("FOURWAY_CANARY", "a secret in the caller's environment")
	result, tree := session(t, id, hostile, 2*time.Minute)
	if result.Report == nil {
		t.Fatalf("no report: crashed %q", result.Crashed)
	}
	if len(result.Report.Tests) != 8 {
		t.Errorf("ran %d tests, want 8: %v", len(result.Report.Tests), result.Report.Tests)
	}
	for test, outcome := range result.Report.Tests {
		if outcome != "passed" {
			t.Errorf("%s %s", test, outcome)
		}
	}
	if _, err := os.Stat(filepath.Join(tree, "planted.py")); err == nil {
		t.Error("the session wrote into the host's tree")
	}
}

func TestATimeoutStopsTheContainer(t *testing.T) {
	// Killing only the docker client would leave the session running, still
	// using CPU and still able to act.
	id := image(t)
	result, _ := session(t, id, "import time\n\ndef test_hang():\n    time.sleep(120)\n", 5*time.Second)
	if result.Crashed != "timeout" {
		t.Fatalf("crashed = %q, want timeout", result.Crashed)
	}
	out, err := exec.Command("docker", "ps", "-aq", "--filter", "ancestor="+id).Output()
	if err != nil {
		t.Fatal(err)
	}
	if left := strings.TrimSpace(string(out)); left != "" {
		t.Errorf("containers still exist after the timeout: %s", left)
	}
}

func TestAForgedReportIsACrash(t *testing.T) {
	// A session can write to the script's stdout; anything that isn't one
	// clean report must read as no evidence, never as a result.
	id := image(t)
	// While pytest runs, the shell's own stdout points at /dev/null, so the
	// session writes to every pipe the shell holds, as an attacker would.
	forge := `import os

def test_forge():
    written = 0
    for fd in os.listdir("/proc/1/fd"):
        if os.readlink(f"/proc/1/fd/{fd}").startswith("pipe:"):
            os.write(os.open(f"/proc/1/fd/{fd}", os.O_WRONLY), b'{"tests": {}')
            written += 1
    assert written
`
	result, _ := session(t, id, forge, 2*time.Minute)
	if result.Crashed != "error" {
		t.Errorf("crashed = %q, want error; report %+v", result.Crashed, result.Report)
	}
}

func TestAMissingImageIsASandboxFailure(t *testing.T) {
	// If a missing image read as a crashed session, every scenario would score
	// as broken and the run would look like a generator failure.
	image(t)
	spec := Spec{Image: "sha256:" + strings.Repeat("0", 64), Tree: t.TempDir(), Timeout: time.Minute, Args: pytestArgs}
	spec.Tree, _ = filepath.EvalSymlinks(spec.Tree)
	if _, err := Run(context.Background(), "docker", spec); err == nil {
		t.Error("Run returned a result for an image that does not exist")
	}
}
