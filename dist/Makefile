TARGET=intenseflow

all: $(TARGET).rc

$(TARGET).ico: $(TARGET).png
	convert -background transparent -define 'icon:auto-resize=16,24,32,64' $^ $@

$(TARGET).rc: $(TARGET).ico
	$(shell echo IDI_ICON1 ICON \"$^\" > $@)
