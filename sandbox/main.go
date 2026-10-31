// Command fourway-sandbox runs one pytest session on one tree inside a
// container with no network, no credentials, and a read-only copy of the
// tree. Decision 0002 requires it before fourway runs scenarios that a model
// wrote from a diff fourway did not author; decision 0003 says why it is Go.
//
// Usage:
//
//	fourway-sandbox image NAME
//	fourway-sandbox run --image ID --tree DIR [--pythonpath DIR]... [--timeout 120s] -- PYTEST_ARGS...
//
// image prints the ID of a local image. run prints one JSON Result on stdout
// and exits 0 whatever the session did; it exits 1 only when the sandbox
// itself fails, and 2 on a usage error.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"
)

type list []string

func (l *list) String() string     { return strings.Join(*l, ",") }
func (l *list) Set(v string) error { *l = append(*l, v); return nil }

func main() {
	os.Exit(run(os.Args[1:]))
}

func run(argv []string) int {
	docker := os.Getenv("FOURWAY_DOCKER")
	if docker == "" {
		docker = "docker"
	}
	if len(argv) == 0 {
		return usage("missing command")
	}
	switch argv[0] {
	case "image":
		if len(argv) != 2 {
			return usage("image takes one image name")
		}
		id, err := ResolveImage(docker, argv[1])
		if err != nil {
			return fail(err)
		}
		fmt.Println(id)
		return 0
	case "run":
		return runSession(docker, argv[1:])
	}
	return usage("unknown command " + argv[0])
}

func runSession(docker string, argv []string) int {
	fs := flag.NewFlagSet("run", flag.ContinueOnError)
	var spec Spec
	var pythonPath list
	fs.StringVar(&spec.Image, "image", "", "image ID (sha256:...)")
	fs.StringVar(&spec.Tree, "tree", "", "directory to mount read-only at /tree")
	fs.Var(&pythonPath, "pythonpath", "tree-relative directory to put on sys.path; repeatable")
	fs.DurationVar(&spec.Timeout, "timeout", 120*time.Second, "wall time for the session")
	if err := fs.Parse(argv); err != nil {
		return 2
	}
	spec.PythonPath, spec.Args = pythonPath, fs.Args()
	// Docker Desktop shares macOS's /private, not the /var symlink into it,
	// so a tree under a temporary directory must be mounted by its real path.
	if spec.Tree != "" {
		real, err := filepath.EvalSymlinks(spec.Tree)
		if err != nil {
			return usage(fmt.Sprintf("--tree: %v", err))
		}
		if spec.Tree, err = filepath.Abs(real); err != nil {
			return usage(fmt.Sprintf("--tree: %v", err))
		}
	}
	if err := spec.Validate(); err != nil {
		return usage(err.Error())
	}
	// An interrupted caller must not leave a container running.
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	result, err := Run(ctx, docker, spec)
	if err != nil {
		return fail(err)
	}
	if err := json.NewEncoder(os.Stdout).Encode(result); err != nil {
		return fail(err)
	}
	return 0
}

func usage(msg string) int {
	fmt.Fprintf(os.Stderr, "fourway-sandbox: %s\n", msg)
	return 2
}

func fail(err error) int {
	fmt.Fprintf(os.Stderr, "fourway-sandbox: %v\n", err)
	return 1
}
