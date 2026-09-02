UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Linux)
MPY_DIR = /mnt/e/micropython
else
MPY_DIR = /e/micropython
endif

SRC_DEV = \
	library.c \
	classes.c \
	module_dev.c

DEV_MOD = T3D_DEV

thumby:
	$(MAKE) -f $(MPY_DIR)/py/dynruntime.mk \
		MPY_DIR=$(MPY_DIR) \
		MOD=$(DEV_MOD) \
		SRC="$(SRC_DEV)" \
		ARCH=armv6m \
		LINK_RUNTIME=1

emulator:
	python3 setup.py build_ext --build-lib build_emulator
	cp build_emulator/T3D_EMU.*.pyd build_emulator/T3D_EMU.pyd


clean:
	rm -rf build-armv6m
	rm -rf build_emulator
	rm -rf build
	rm -rf *.egg-info
	rm -f $(DEV_MOD).mpy
	rm -f *.pyd


.PHONY: thumby emulator clean