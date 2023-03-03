SEAL := seal
OUTPUT_DIR := teal
SEAL_FLAGS := compile

.PHONY: clean build

build: $(OUTPUT_DIR) $(patsubst %.seal,$(OUTPUT_DIR)/%.teal,$(wildcard *.seal))

$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

$(OUTPUT_DIR)/%.teal: %.seal
	$(SEAL) $(SEAL_FLAGS) $< > $@

clean:
	rm -rf $(OUTPUT_DIR)
