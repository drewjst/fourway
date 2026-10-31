package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os/exec"
	"path"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

const (
	treeMount = "/tree"
	// The report goes to the container's tmpfs and comes back on stdout, so
	// the container has no writable host mount it could fill or plant files in.
	reportPath = "/tmp/fourway-report.json"
	// Larger than any report a real session writes, small enough to hold in memory.
	maxReport = 16 << 20
	maxStderr = 64 << 10
	nobody    = "65534:65534"
)

// pytest's own output goes nowhere: the report is the only thing read back,
// and the session's exit status says nothing the report doesn't.
const script = `python -m pytest "$@" >/dev/null 2>&1; cat ` + reportPath + ` 2>/dev/null; exit 0`

var imageID = regexp.MustCompile(`^sha256:[0-9a-f]{64}$`)

// Spec describes one pytest session on one tree.
type Spec struct {
	Image      string        // image ID, never a tag, so every run in a session uses the same image
	Tree       string        // host directory, mounted read-only at /tree
	PythonPath []string      // tree-relative directories put on sys.path after /tree
	Timeout    time.Duration // wall time for the whole container, startup included
	Args       []string      // arguments to python -m pytest
}

// Report is what fourway's pytest plugin writes; see src/fourway/pytest_plugin.py.
type Report struct {
	Tests         map[string]string `json:"tests"`
	CollectErrors []string          `json:"collect_errors"`
	ExitStatus    int               `json:"exitstatus"`
}

// Result is one session's outcome. Crashed is "timeout" or "error" when the
// session produced no usable report, matching the local runner's RunReport.
type Result struct {
	Image   string  `json:"image"`
	Report  *Report `json:"report"`
	Crashed string  `json:"crashed,omitempty"`
}

// Validate refuses a spec the docker command line could misread.
func (s Spec) Validate() error {
	if !imageID.MatchString(s.Image) {
		return fmt.Errorf("--image must be an image ID (sha256:...), not %q; resolve a tag with fourway-sandbox image", s.Image)
	}
	if !filepath.IsAbs(s.Tree) {
		return fmt.Errorf("--tree must be absolute: %q", s.Tree)
	}
	// --mount is comma-separated key=value pairs.
	if strings.ContainsAny(s.Tree, ",\"\n") {
		return fmt.Errorf("--tree contains a comma, quote, or newline: %q", s.Tree)
	}
	for _, p := range s.PythonPath {
		if !filepath.IsLocal(p) || strings.ContainsAny(p, ":\n") {
			return fmt.Errorf("--pythonpath must be a relative directory inside the tree: %q", p)
		}
	}
	if s.Timeout <= 0 {
		return fmt.Errorf("--timeout must be positive")
	}
	return nil
}

// dockerArgs is the whole isolation policy. Decision 0002 requires no network,
// no credentials, and a read-only copy of the tree; the rest limits what a
// session can do inside the container.
func dockerArgs(s Spec, name string) []string {
	pythonPath := []string{treeMount}
	for _, p := range s.PythonPath {
		pythonPath = append(pythonPath, path.Join(treeMount, filepath.ToSlash(p)))
	}
	args := []string{
		"run", "--rm", "--name", name,
		// A missing image is a sandbox failure, not a reason to reach a registry.
		"--pull", "never",
		"--network", "none",
		// docker run passes no host environment variables unless asked; these
		// are the only ones the session gets beyond the image's own.
		"--env", "PYTHONPATH=" + strings.Join(pythonPath, ":"),
		"--env", "PYTHONHASHSEED=0",
		"--env", "PYTHONDONTWRITEBYTECODE=1",
		"--env", "HOME=/tmp",
		"--env", "FOURWAY_REPORT=" + reportPath,
		"--mount", "type=bind,src=" + s.Tree + ",dst=" + treeMount + ",readonly",
		"--read-only",
		"--tmpfs", "/tmp:rw,nosuid,nodev,size=256m",
		"--workdir", treeMount,
		"--user", nobody,
		"--cap-drop", "ALL",
		"--security-opt", "no-new-privileges",
		"--pids-limit", "512",
		"--memory", "2g",
		"--cpus", "2",
		s.Image,
		"sh", "-c", script, "fourway-run",
	}
	return append(args, s.Args...)
}

// Run executes one session. An error means the sandbox itself failed, for
// example because Docker is down or the image is missing; it is never a
// session outcome, so a broken sandbox can't read as a broken scenario.
func Run(ctx context.Context, docker string, s Spec) (Result, error) {
	if err := s.Validate(); err != nil {
		return Result{}, err
	}
	name, err := containerName()
	if err != nil {
		return Result{}, err
	}
	stdout := &capped{limit: maxReport}
	stderr := &capped{limit: maxStderr}
	cmd := exec.Command(docker, dockerArgs(s, name)...)
	cmd.Stdout, cmd.Stderr = stdout, stderr
	if err := cmd.Start(); err != nil {
		return Result{}, fmt.Errorf("start docker: %w", err)
	}
	done := make(chan error, 1)
	go func() { done <- cmd.Wait() }()

	timer := time.NewTimer(s.Timeout)
	defer timer.Stop()
	select {
	case err = <-done:
	case <-timer.C:
		// Killing the docker client would leave the container running.
		kill(docker, name)
		<-done
		return Result{Image: s.Image, Crashed: "timeout"}, nil
	case <-ctx.Done():
		kill(docker, name)
		<-done
		return Result{}, ctx.Err()
	}

	var exit *exec.ExitError
	if errors.As(err, &exit) {
		// docker run exits 125 when the daemon refuses the container, and 126 or
		// 127 when it can't start the command. The script itself always exits 0,
		// so any other status means the container was killed, for example by
		// the memory limit.
		switch exit.ExitCode() {
		case 125, 126, 127:
			return Result{}, fmt.Errorf("docker run failed (exit %d): %s", exit.ExitCode(), bytes.TrimSpace(stderr.Bytes()))
		}
		return Result{Image: s.Image, Crashed: "error"}, nil
	} else if err != nil {
		return Result{}, fmt.Errorf("wait for docker: %w", err)
	}
	report, ok := parseReport(stdout)
	if !ok {
		return Result{Image: s.Image, Crashed: "error"}, nil
	}
	return Result{Image: s.Image, Report: report}, nil
}

// parseReport reads what the session printed. The session controls those
// bytes, so an oversized, malformed, or incomplete report counts as a crash.
func parseReport(out *capped) (*Report, bool) {
	if out.overflow || out.Len() == 0 {
		return nil, false
	}
	var r Report
	dec := json.NewDecoder(bytes.NewReader(out.Bytes()))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&r); err != nil || dec.More() || r.Tests == nil || r.CollectErrors == nil {
		return nil, false
	}
	return &r, true
}

// ResolveImage returns the ID of a local image, so a session pins the exact
// image that the evidence ledger records.
func ResolveImage(docker, name string) (string, error) {
	out, err := exec.Command(docker, "image", "inspect", "--format", "{{.Id}}", name).Output()
	if err != nil {
		return "", fmt.Errorf("image %q not found; build it with: docker build -f sandbox/Dockerfile -t %s .", name, name)
	}
	id := strings.TrimSpace(string(out))
	if !imageID.MatchString(id) {
		return "", fmt.Errorf("docker returned an unexpected image ID %q", id)
	}
	return id, nil
}

func kill(docker, name string) {
	// The container may have exited already, so the error says nothing useful.
	_ = exec.Command(docker, "kill", name).Run()
}

func containerName() (string, error) {
	b := make([]byte, 8)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return "fourway-" + hex.EncodeToString(b), nil
}

// capped keeps the first limit bytes written to it and discards the rest.
type capped struct {
	bytes.Buffer
	limit    int
	overflow bool
}

func (c *capped) Write(p []byte) (int, error) {
	if room := c.limit - c.Len(); len(p) > room {
		c.overflow = true
		c.Buffer.Write(p[:max(room, 0)])
		return len(p), nil
	}
	return c.Buffer.Write(p)
}
