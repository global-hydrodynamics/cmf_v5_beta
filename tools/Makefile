##################################################
# Shared v5 settings; never fall back to the legacy adm/ configuration.
ifeq ($(wildcard ../config/Mkinclude),)
$(error CaMa-Flood v5 configuration missing: ../config/Mkinclude. Review config/README.md and copy a reviewed template to config/Mkinclude)
endif
include   ../config/Mkinclude
##################################################
TARGETS=\
igetday \

.PHONY: all clean
all: $(TARGETS)

clean:
	$(RM) -rf *.o *.s core *~ *trace *.mod *.dSYN $(TARGETS)

.SUFFIXES : .F90
.F90:
	$(FC) $(FFLAGS) $(LFLAGS) $(LFLAG) $(INC) $^ -o $@

