.PHONY: all
all: example

.PHONY: example
example:
		python example.py
			gcc -o out out.c
				./out

.PHONY: stack_based
stack_based:
	python3 stack_based.py
	gcc -o out out.c
	./out

.PHONY: build
build:
ifeq ($(TARGET), example)
	$(MAKE) example
else ifeq ($(TARGET), stack_based)
	$(MAKE) stack_based
endif

