files_directory="$1"
shopt -s nullglob
for wav in "$files_directory"/*.wav; do
    fname=$(basename "$wav")
    python3 embed_md.py -dadir "$files_directory" -daid $fname
    sleep 0.2
done
