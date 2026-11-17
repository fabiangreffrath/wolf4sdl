TARGET=intenseflow

all: $(TARGET).rc

$(TARGET).xpm: $(TARGET).png
	convert $^ $@

$(TARGET).png: $(TARGET).svg
	inkscape --export-png=$@ $^

$(TARGET).ico: $(TARGET).svg
	convert -background transparent -define 'icon:auto-resize=16,24,32,64' $^ $@

$(TARGET).rc: $(TARGET).ico
	$(shell echo IDI_ICON1 ICON DISCARDABLE \"$^\" > $@)
