all:
	bazel build //src/...

clean:
	bazel clean

test:
	bazel test //src:vulpes_tests
