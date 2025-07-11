all:
	cmake -B build
	cmake --build build

clean:
	rm -rf build

test:
	build/vm test/test.vm

