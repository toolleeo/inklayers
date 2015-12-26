python svg-export-layers.py -c bug2-closer.json bug2-closer.svg
# ./svg-objects-export.py --xpath "//svg:g[@inkscape:groupmode='layer']" --extra '--export-area-page --export-id-only' my-image.svg
gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=out.pdf bug2-closer-?.pdf
