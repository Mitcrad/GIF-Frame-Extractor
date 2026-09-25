# GIF Compression Assistant

This tool significantly reduces GIF size by decreasing the number of animation frames without affecting image quality. It merges the playback time of skipped frames to the previous kept frame, so the total animation duration and speed remain the same, but the motion may look a bit jumpy.

## Easiest Way to Use (Windows)

1. Click "Select File" to pick your GIF.
2. Drag the "Compression Level" slider (`4` is a recommended starting point).
3. Click "Start Compression".

The interface will show the original frame count, estimated output frame count, processing status, and the final space saved.

## Command Line Usage (Optional)

If you prefer the command line, you can also double-click `CompressGIF.cmd`, paste the full path of the GIF, and then enter the retention interval:

- `3`: Keep 1 frame out of every 3, smoother animation
- `4`: Usually a good balance between size and smoothness
- `6`: More compression, motion looks jumpier

The output file will be saved alongside the original GIF, named `OriginalFileName_reduced.gif`. You can also drag the GIF directly onto the script and follow the prompts.

## Notes

- Reducing frames usually shrinks the file significantly, but the final size also depends on the image content and color changes.
- This tool does not scale pixel dimensions; if you need to drastically reduce a 100MB GIF, it’s recommended to first remove frames, then resize proportionally or convert to MP4/WebM.
