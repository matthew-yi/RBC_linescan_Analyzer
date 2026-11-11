// ============================================================
//  RBC Linescan Analyzer  v15
//  Fiji/ImageJ Macro
//
//  ALGORITHM:
//  1. Read companion .xml file (PrairieView) for scan metadata:
//     scanLinePeriod, micronsPerPixel, framePeriod, lineLength.
//     Falls back to manual entry if no .xml is found.
//  2. Sweep angles -MAX_ANGLE_DEG to +MAX_ANGLE_DEG.
//     Score each by projection VARIANCE — correct angle gives
//     sharp alternating bright/dark bands = high variance.
//  3. Sign disambiguation: compare fine-sigma variance at +slope
//     vs -slope; higher variance = correct dark-band alignment.
//  4. AUTO-SIGMA peak detection:
//     - Sweep sigma [0.5..12], find first stable plateau (<20% change).
//     - Dense/clean images: use sigma=0.5 directly.
//     - Blurry/sparse images: scale sigma and min_dist to period.
//  5. Draw tilted red lines on the image at each detected RBC.
//  6. Compute and report:
//       RBC flux       = count / duration  (RBCs/s)
//       RBC velocity   = (µm/pixel / s/line) / tan(angle)  (µm/s)
//       Lineal density = flux / velocity  (RBCs/µm)
//       Inter-RBC CV   = std(intervals) / mean(intervals)
//
//  NOTE ON ACCURACY:
//  Images with very few RBCs (<20) in steep diagonal lines may
//  over-count by 20-50% because secondary brightness patterns
//  between RBC lines create extra detected peaks. If this affects
//  your data, raise REL_THRESHOLD to 0.30-0.40.
// ============================================================

// ── USER-TUNABLE PARAMETERS ─────────────────────────────────

// Relative prominence threshold (0.0–1.0).
// Each peak must exceed its LOCAL floor by this fraction of the
// local dynamic range.
// Default 0.18 works well for dense images (many RBCs, clear bands).
// Sparse images (nLoose < 60) use a higher threshold (0.30) automatically
// to reject noise peaks that appear when baseline subtraction is off.
var REL_THRESHOLD = 0.18;

// Threshold used for sparse-vessel final detection (nLoose < 60).
// Higher value rejects weak noise peaks while still catching real RBC bands.
var SPARSE_REL_THRESHOLD = 0.30;

// Smoothing sigma used for angle-scoring (not peak detection).
// Detection sigma is chosen automatically.
var SMOOTH_SIGMA = 2.0;

// Minimum window size (rows) for local baseline calculation.
var LOCAL_WINDOW = 30;

// Minimum row separation between two RBC detections.
var MIN_DISTANCE = 3;

// Edge zone (rows). Lines this close to top/bottom edges only
// need ONE bright inward neighbour to count.
var EDGE_ZONE = 30;

// Maximum line angle to search (degrees from horizontal).
var MAX_ANGLE_DEG = 80;

// Coarse angle sweep step (degrees).
var ANGLE_STEP_COARSE = 2.0;

// Fine refinement step (degrees) around the best coarse angle.
var ANGLE_STEP_FINE = 0.2;

// ── GLOBAL STATE (set by detectRBCLines, read by caller) ────
var lastAngleDeg   = 0;     // best line angle found (degrees)
var lastPeakRows   = 0;     // sentinel — replaced with peak array after detection
var lastPeakCount  = 0;     // number of valid peaks stored
var lastPlasmaFlag = false; // true if primary detection was flagged (fallback used)
var lastQCString   = "OK";  // "OK" or "FLAG (fallback used)"

// ── MAIN MENU ────────────────────────────────────────────────
setBatchMode(true);
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/7.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/7.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/8_LineScan-04102026-1255-8539_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/7.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/11.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/11.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/12_LineScan-04102026-1255-8544_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/11.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/15.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/15.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/16_LineScan-04102026-1255-8547_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/15.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/19.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/19.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/20_LineScan-04102026-1255-8552_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/19.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/23.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/23.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/24_LineScan-04102026-1255-8556_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/23.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/27.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/27.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/28_LineScan-04102026-1255-8562_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/27.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/31.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/31.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/32_LineScan-04102026-1255-8573_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/31.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/35.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/35.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/36_LineScan-04102026-1255-8577_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/35.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/39.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/39.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/40_LineScan-04102026-1255-8581_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/39.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/43.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/43.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/44_LineScan-04102026-1255-8587_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/43.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/47.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/47.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/48_LineScan-04102026-1255-8591_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/47.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/51.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/51.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/52_LineScan-04102026-1255-8595_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/51.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/55.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/55.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/56_LineScan-04102026-1255-8598_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/55.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/59.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/59.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/60_LineScan-04102026-1255-8603_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/59.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/63.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/63.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/64_LineScan-04102026-1255-8607_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/63.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/67.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/67.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/68_LineScan-04102026-1255-8612_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/67.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/71.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/71.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/72_LineScan-04102026-1255-8616_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/71.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/75.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/75.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/76_LineScan-04102026-1255-8618_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/75.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/79.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/79.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/80_LineScan-04102026-1255-8630_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/79.txt");
open("/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/analysis_input/83.tif");
if (nSlices>1) exit("Multi-plane TIFF detected. Split into individual 2D linescans before analysis.");
imgID=getImageID();
run("Duplicate...", "title=_preview_"); run("8-bit");
saveAs("PNG", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/previews/83.png"); close();
lastAngleDeg=0; lastPeakCount=0; lastPeakRows=newArray(1); lastPeakRows[0]=-1; lastQCString="OK";
count=detectRBCLines(imgID, true);
saveAs("Tiff", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/RBC_Annotated/84_LineScan-04102026-1255-8636_Cycle00001_Ch3_000001.ome.tif_annotated.tif"); close();
text=""+lastAngleDeg+"\n"+lastQCString+"\n";
for (p=0;p<lastPeakCount;p++) text=text+lastPeakRows[p]+"\n";
File.saveString(text, "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/detections/83.txt");
File.saveString("complete", "/Users/matthewyi/Documents/RBC Linescan Analyzer/validation_ag8/batch_1_complete.txt");
setBatchMode(false);
// ── SINGLE MODE ──────────────────────────────────────────────
function runSingleMode() {
    if (nImages == 0) {
        path = File.openDialog("Select a linescan image");
        if (path == "") exit("No file selected.");
        open(path);
    }
    imgID    = getImageID();
    imgName  = getTitle();
    imgPath  = getDirectory("image") + imgName;

    // Try to read metadata from companion .xml file
    meta = readXMLMeta(imgPath);
    // meta = [duration, scanLinePeriod, micronsPerPixel, lineLength_um]
    // Values are -1 if not found.

    duration = meta[0];
    if (duration <= 0) duration = promptForDuration(imgName);

    // Run detection — also returns peak row positions via global var
    count    = detectRBCLines(imgID, true);
    angleDeg = lastAngleDeg;        // set by detectRBCLines

    // Compute derived metrics
    metrics = computeMetrics(count, duration, angleDeg, meta, lastPeakRows, lastPeakCount);
    // metrics = [flux, velocity_um_s, lineal_density, cv_intervals]

    showResultsDialog(imgName, count, duration, angleDeg, meta, metrics);
    logResult(imgName, count, duration, angleDeg, meta, metrics);
}

// ── BATCH MODE ───────────────────────────────────────────────
function runBatchMode() {
    inputDir = getDirectory("Select folder containing linescan images");
    if (inputDir == "") exit("No folder selected.");

    outputDir = inputDir + "RBC_Annotated" + File.separator;
    if (!File.exists(outputDir)) File.makeDirectory(outputDir);

    // Duration fallback: only asked when no .xml found
    Dialog.create("Batch Settings");
    Dialog.addMessage("If a .xml metadata file exists alongside each image,\nduration and scale are read automatically.\nOtherwise, enter a fallback duration below.");
    Dialog.addNumber("Fallback duration (s):", 1.0, 4, 8, "s");
    Dialog.show();
    fallbackDuration = Dialog.getNumber();

    exts      = newArray(".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp");
    list      = getFileList(inputDir);
    processed = 0;

    if (isOpen("RBC Results")) { selectWindow("RBC Results"); run("Close"); }

    for (i = 0; i < list.length; i++) {
        fname = list[i];
        if (!isImageFile(fname, exts)) continue;
        imgPath = inputDir + fname;
        open(imgPath);
        imgID = getImageID();

        meta = readXMLMeta(imgPath);
        duration = meta[0];
        if (duration <= 0) duration = fallbackDuration;

        count    = detectRBCLines(imgID, true);
        angleDeg = lastAngleDeg;

        metrics  = computeMetrics(count, duration, angleDeg, meta, lastPeakRows, lastPeakCount);

        baseName = File.getNameWithoutExtension(fname);
        saveAs("Tiff", outputDir + baseName + "_annotated.tif");
        close();
        logResult(fname, count, duration, angleDeg, meta, metrics);
        processed++;
    }

    showMessage("Batch complete!\n" + processed + " image(s) processed.\n" +
                "Annotated images saved to:\n" + outputDir);
}

// ── CORE DETECTION ───────────────────────────────────────────
function detectRBCLines(imgID, annotate) {
    selectImage(imgID);
    W = getWidth();
    H = getHeight();

    // Read image pixels, normalize 0-1
    run("Duplicate...", "title=_rbcWork_");
    workID = getImageID();
    run("8-bit");

    pixels = newArray(H * W);
    pixSum = 0;
    for (y = 0; y < H; y++) {
        for (x = 0; x < W; x++) {
            v = getPixel(x, y);
            pixels[y * W + x] = v;
            pixSum += v;
        }
    }
    close();

    minPx = pixels[0]; maxPx = pixels[0];
    for (k = 1; k < H * W; k++) {
        if (pixels[k] < minPx) minPx = pixels[k];
        if (pixels[k] > maxPx) maxPx = pixels[k];
    }
    pxRange = maxPx - minPx;
    if (pxRange == 0) { lastQCString="BLANK IMAGE"; return 0; }

    globalMean = pixSum / (H * W);
    normGlobalMean = (globalMean - minPx) / pxRange;
    for (k = 0; k < H * W; k++) {
        pixels[k] = (pixels[k] - minPx) / pxRange;
    }

    // ── Angle sweep: maximize projection variance ────────────
    bestVar   = -1;
    bestSlope = 0;

    nCoarse = round(2 * MAX_ANGLE_DEG / ANGLE_STEP_COARSE) + 1;
    for (step = 0; step < nCoarse; step++) {
        angleDeg = -MAX_ANGLE_DEG + step * ANGLE_STEP_COARSE;
        slope    = tan(angleDeg * PI / 180.0);
        proj     = buildProjection(pixels, H, W, slope, normGlobalMean);
        v        = projVariance(proj, H);
        if (v > bestVar) { bestVar = v; bestSlope = slope; }
    }

    coarseAngle = atan(bestSlope) * 180.0 / PI;
    nFine = round(2 * ANGLE_STEP_COARSE / ANGLE_STEP_FINE) + 1;
    for (step = 0; step < nFine; step++) {
        angleDeg = coarseAngle - ANGLE_STEP_COARSE + step * ANGLE_STEP_FINE;
        slope    = tan(angleDeg * PI / 180.0);
        proj     = buildProjection(pixels, H, W, slope, normGlobalMean);
        v        = projVariance(proj, H);
        if (v > bestVar) { bestVar = v; bestSlope = slope; }
    }

    // ── Sign disambiguation ──────────────────────────────────
    // Use projection variance (sigma=0.5) to pick the correct slope sign.
    // The correct slope aligns the dark bands → sharper projection → higher variance.
    // Spacing score biases toward sparse detections and fails on dense images.
    projPos = buildProjection(pixels, H, W,  bestSlope, normGlobalMean);
    projNeg = buildProjection(pixels, H, W, -bestSlope, normGlobalMean);

    // Compute variance at fine sigma to capture sharp bands
    varPos = projVarianceFine(projPos, H);
    varNeg = projVarianceFine(projNeg, H);

    // Choose projection direction
    if (varPos >= varNeg) {
        bestProj = projPos;
    } else {
        bestSlope = -bestSlope;
        bestProj  = projNeg;
    }

    // ── Pass 1: primary detection (Rule 0 / Rule 2a / plateau) ──
    centers = autoSigmaDetect(bestProj, H);
    if (centers[0] == -1) count = 0; else count = centers.length;
    bestAngleDeg = atan(bestSlope) * 180.0 / PI;
    print("Pass1: " + count + " RBCs at " + d2s(bestAngleDeg, 1) + "°");

    // ── Plasma / noise check on primary result ───────────────────
    // Spacing CV > 0.55 or implied period < 3.5 lines = suspect count.
    lastPlasmaFlag = false;
    lastQCString   = "OK";
    if (count > 1 && centers[0] != -1) {
        spacingSum = 0; spacingSumSq = 0;
        for (pi = 0; pi < count - 1; pi++) {
            sp = centers[pi + 1] - centers[pi];
            spacingSum   += sp;
            spacingSumSq += sp * sp;
        }
        spacingMean   = spacingSum / (count - 1);
        spacingVar    = (spacingSumSq / (count - 1)) - (spacingMean * spacingMean);
        spacingStd    = sqrt(maxOf(spacingVar, 0));
        spacingCV     = spacingStd / (spacingMean + 0.001);
        impliedPeriod = H / count;
        lastPlasmaFlag = (spacingCV > 0.55) || (impliedPeriod < 3.5);
        print("PlasmaCheck: spacingCV=" + d2s(spacingCV, 3) +
              " period=" + d2s(impliedPeriod, 1) + " flag=" + lastPlasmaFlag);
    }

    // ── Pass 2: V9 fallback if primary was flagged ───────────────
    // V9's simpler plateau algorithm is conservative and avoids the
    // over-detection that triggers the flag on sparse / plasma vessels.
    // The flag is kept in the output so the row is still visible for review.
    if (lastPlasmaFlag) {
        print("Pass1 flagged — running V9 fallback");
        centersV9 = autoSigmaDetectV9(bestProj, H);
        if (centersV9[0] == -1) countV9 = 0; else countV9 = centersV9.length;
        print("Pass2 (V9 fallback): " + countV9 + " RBCs");
        centers = centersV9;
        count   = countV9;
        lastQCString = "FLAG (fallback used)";
    }

    if (annotate && count > 0 && centers[0] != -1) {
        selectImage(imgID);
        run("RGB Color");
        setForegroundColor(255, 0, 0);
        for (i = 0; i < count; i++) {
            y0 = centers[i];
            for (x = 0; x < W; x++) {
                drawY = round(y0 - x * bestSlope);
                if (drawY >= 0 && drawY < H) {
                    makeRectangle(x, drawY, 1, 1);
                    run("Fill", "slice");
                }
            }
        }
        run("Select None");
    }

    // Store results for caller to read
    lastAngleDeg  = bestAngleDeg;
    lastPeakCount = count;
    if (count > 0 && centers[0] != -1) {
        lastPeakRows = centers;   // array of row positions
    } else {
        sentinel = newArray(1); sentinel[0] = -1;
        lastPeakRows = sentinel;
    }

    return count;
}

// ── AUTO-SIGMA + PERIOD-GUIDED DETECTION ─────────────────────
// Fixes double-counting (2-3 lines per wide band) by auto-scaling
// both sigma and min_dist to the image's true line period.
//
// Rule 1 — Dense/clean (drop 0.5→1.0 < 15%): lines are narrow and
//   regularly spaced. Use sigma=0.5 directly. Period = H/n05.
//
// Rule 2 — Sub-peaks present (drop >= 15%): find the LONGEST stable
//   run in the sigma sweep (< 20% change per step). The plateau count
//   gives the best period estimate.
//
// Then: sigma = period/8, min_dist = period*0.4, both capped sensibly.
// This handles dense (215, period=7), moderate (211, period=42),
// and sparse (202-207, period=100-250) images correctly.
//
function autoSigmaDetect(proj, H) {
    sigmaLadder = newArray(0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0);
    nLadder     = sigmaLadder.length;

    // Rule 0 — Very dense image check.
    // Count peaks at sigma=0.5 with min_dist=1 vs min_dist=3.
    // If the tight-distance count is >25% higher, RBCs are packed
    // closer than 3 lines apart. Use sigma=0.5, min_dist=1 directly
    // and skip the plateau logic entirely.
    tmpTight = detectAtSigmaFixed(proj, H, 0.5, 1);
    nTight   = tmpTight.length;
    if (nTight == 1 && tmpTight[0] == -1) nTight = 0;
    tmpLoose = detectAtSigmaFixed(proj, H, 0.5, MIN_DISTANCE);
    nLoose   = tmpLoose.length;
    if (nLoose == 1 && tmpLoose[0] == -1) nLoose = 0;
    if (nLoose < 1) nLoose = 1;
    densityBoost = (nTight - nLoose) / nLoose;
    // Only trigger Rule 0 when:
    //   1. nLoose is already high (>120), meaning the image genuinely has
    //      many RBCs even before tight detection — sparse noisy images
    //      typically have nLoose < 80 even when nTight explodes with noise.
    //   2. The boost ratio is modest (1.25-2.5x) — a genuine dense vessel
    //      recovers a fraction of missed peaks, not 10-20x explosion.
    //      A sparse image with noise between bands gets nTight >> nLoose*5.
    print("Rule0: nLoose=" + nLoose + " nTight=" + nTight + " boost=" + d2s(densityBoost, 2));
    if (nLoose > 120 && densityBoost > 0.25 && densityBoost < 2.5) {
        print("Rule0: TRIGGERED dense path — using baseline subtraction");
        // Dense vessel confirmed by raw nLoose > 120 → baseline subtraction is safe
        finalResult = detectAtSigmaFixedDense(proj, H, 0.5, 1);
        return finalResult;
    } else {
        print("Rule0: skipped");
    }

    // Compute count at each sigma (coarse, dist=3).
    // IMPORTANT: never subscript a function-return array directly in ImageJ macro.
    // Always assign to a local variable first, then check the sentinel.
    counts = newArray(nLadder);
    for (si = 0; si < nLadder; si++) {
        tmpPks = detectAtSigmaFixed(proj, H, sigmaLadder[si], MIN_DISTANCE);
        tmpN   = tmpPks.length;
        if (tmpN == 1 && tmpPks[0] == -1) tmpN = 0;
        counts[si] = tmpN;
    }

    // Rule 1: if drop sigma=0.5→1.0 is tiny, lines are already clean
    n05 = counts[0]; n10 = counts[1];
    if (n05 < 1) n05 = 1;
    drop0510 = (n05 - n10) / n05;
    if (drop0510 < 0.15) {
        // Dense clean image — use sigma=0.5 directly
        period = H / n05;
    } else {
        // Rule 2a — Continuously declining counts mean no real plateau.
        // If the finest scale (sigma=0.5) count is more than 3x the coarsest
        // (sigma=12), the image is dense and getting coarser only loses peaks.
        // Use sigma=0.5 directly ONLY when nLoose >= 60 — if nLoose is low,
        // the image is sparse or plasma-dominated and fine-scale detection
        // just finds noise sub-peaks, producing wildly inflated counts.
        // With few coherent bands (nLoose < 60), fall through to plateau logic.
        nFinest  = counts[0];
        nCoarset = counts[nLadder - 1];
        if (nCoarset < 1) nCoarset = 1;
        if (nFinest / nCoarset > 3.0 && nLoose >= 60) {
            period = H / nFinest;
            print("Rule2a: triggered nFinest=" + nFinest + " nCoarset=" + nCoarset + " nLoose=" + nLoose);
        } else {
            // Rule 2b: find longest stable run (< 20% change per step)
            bestRunLen   = 1;
            bestRunStart = 0;
            runLen = 1; runStart = 0;
            for (si = 1; si < nLadder; si++) {
                prev = counts[si - 1]; curr = counts[si];
                if (prev > 0 && abs(curr - prev) / prev < 0.20) {
                    runLen++;
                } else {
                    if (runLen > bestRunLen) {
                        bestRunLen   = runLen;
                        bestRunStart = runStart;
                    }
                    runStart = si; runLen = 1;
                }
            }
            if (runLen > bestRunLen) {
                bestRunLen   = runLen;
                bestRunStart = runStart;
            }
            bestIdx   = bestRunStart + round(bestRunLen / 2);
            if (bestIdx >= nLadder) bestIdx = nLadder - 1;
            plateauN  = counts[bestIdx];
            if (plateauN < 1) plateauN = 1;
            period = H / plateauN;
        }
    }

    // Derive detection parameters from period
    sigma2   = maxOf(0.5,  period / 8.0);
    minDist2 = maxOf(3,    round(period * 0.40));
    // Cap: sigma must not span more than half a period
    if (sigma2 > period * 0.45) sigma2 = period * 0.45;

    // Apply baseline subtraction ONLY for confirmed dense vessels (nLoose > 60).
    // For sparse vessels, baseline at sigma=200 captures the real RBC peaks as
    // background and destroys the signal, creating noise that inflates counts.
    // Also raise REL_THRESHOLD for sparse detection to reject noise peaks.
    if (nLoose > 60) {
        print("Final detect: dense vessel (nLoose=" + nLoose + "), baseline ON, sigma=" + d2s(sigma2,2) + " minDist=" + minDist2);
        finalResult = detectAtSigmaFixedDense(proj, H, sigma2, minDist2);
    } else {
        print("Final detect: sparse vessel (nLoose=" + nLoose + "), baseline OFF, higher threshold, sigma=" + d2s(sigma2,2) + " minDist=" + minDist2);
        // Temporarily raise threshold to reject noise sub-peaks
        savedThreshold = REL_THRESHOLD;
        REL_THRESHOLD  = SPARSE_REL_THRESHOLD;
        finalResult = detectAtSigmaFixed(proj, H, sigma2, minDist2);
        REL_THRESHOLD  = savedThreshold;
    }
    return finalResult;
}

// NOTE: ImageJ macro language has no true local scope — all variables
// are effectively global within a macro run.  To avoid wrapper functions
// clobbering each other's return arrays, we inline detectAtSigmaCore
// rather than calling it through a wrapper.  The two functions below are
// identical except for the doBaseline branch.

// detectAtSigmaFixed: probe / sparse-vessel detection — NO baseline subtraction
function detectAtSigmaFixed(proj, H, sigma, minDist) {
    projInv_f = normalizeAndInvert(proj, H);
    projSm_f  = gaussianSmooth1D(projInv_f, sigma);
    winSize_f = maxOf(LOCAL_WINDOW, round(sigma * 8));
    lMin_f    = localMinFilter(projSm_f, winSize_f, H);
    lMax_f    = localMaxFilter(projSm_f, winSize_f, H);
    res_f     = findPeaksAdaptive(projSm_f, lMin_f, lMax_f,
                                   REL_THRESHOLD, minDist, EDGE_ZONE, H);
    if (res_f.length == 0) {
        sen_f = newArray(1); sen_f[0] = -1; return sen_f;
    }
    return res_f;
}

// detectAtSigmaFixedDense: confirmed-dense final detection — WITH baseline subtraction
function detectAtSigmaFixedDense(proj, H, sigma, minDist) {
    baseSmooth_d  = gaussianSmooth1D(proj, 200.0);
    projCorr_d    = newArray(H);
    for (bi_d = 0; bi_d < H; bi_d++) {
        projCorr_d[bi_d] = proj[bi_d] - baseSmooth_d[bi_d];
    }
    projInv_d = normalizeAndInvert(projCorr_d, H);
    projSm_d  = gaussianSmooth1D(projInv_d, sigma);
    winSize_d = maxOf(LOCAL_WINDOW, round(sigma * 8));
    lMin_d    = localMinFilter(projSm_d, winSize_d, H);
    lMax_d    = localMaxFilter(projSm_d, winSize_d, H);
    res_d     = findPeaksAdaptive(projSm_d, lMin_d, lMax_d,
                                   REL_THRESHOLD, minDist, EDGE_ZONE, H);
    if (res_d.length == 0) {
        sen_d = newArray(1); sen_d[0] = -1; return sen_d;
    }
    return res_d;
}

// ── V9 FALLBACK DETECTION ────────────────────────────────────
// Exact copy of V9's autoSigmaDetect: sigma ladder → longest stable
// plateau → period-guided final detection.  No Rule 0, no Rule 2a,
// no baseline subtraction.  Used when the primary pass is flagged.
// Variable names use _v9 suffix to avoid IJM global-scope collisions.
function autoSigmaDetectV9(proj_v9, H_v9) {
    sigLad_v9 = newArray(0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0);
    nLad_v9   = sigLad_v9.length;

    cnts_v9 = newArray(nLad_v9);
    for (si_v9 = 0; si_v9 < nLad_v9; si_v9++) {
        tmp_v9  = detectAtSigmaFixed(proj_v9, H_v9, sigLad_v9[si_v9], MIN_DISTANCE);
        tmpN_v9 = tmp_v9.length;
        if (tmpN_v9 == 1 && tmp_v9[0] == -1) tmpN_v9 = 0;
        cnts_v9[si_v9] = tmpN_v9;
    }

    // Rule 1: tiny drop 0.5→1.0 means clean dense image
    n05_v9 = cnts_v9[0]; n10_v9 = cnts_v9[1];
    if (n05_v9 < 1) n05_v9 = 1;
    drop_v9 = (n05_v9 - n10_v9) / n05_v9;
    if (drop_v9 < 0.15) {
        period_v9 = H_v9 / n05_v9;
    } else {
        // Find longest stable run (<20% change per step)
        bRL_v9 = 1; bRS_v9 = 0;
        rL_v9  = 1; rS_v9  = 0;
        for (si_v9 = 1; si_v9 < nLad_v9; si_v9++) {
            pv_v9 = cnts_v9[si_v9 - 1]; cv_v9 = cnts_v9[si_v9];
            if (pv_v9 > 0 && abs(cv_v9 - pv_v9) / pv_v9 < 0.20) {
                rL_v9++;
            } else {
                if (rL_v9 > bRL_v9) { bRL_v9 = rL_v9; bRS_v9 = rS_v9; }
                rS_v9 = si_v9; rL_v9 = 1;
            }
        }
        if (rL_v9 > bRL_v9) { bRL_v9 = rL_v9; bRS_v9 = rS_v9; }
        bi_v9 = bRS_v9 + round(bRL_v9 / 2);
        if (bi_v9 >= nLad_v9) bi_v9 = nLad_v9 - 1;
        pN_v9 = cnts_v9[bi_v9];
        if (pN_v9 < 1) pN_v9 = 1;
        period_v9 = H_v9 / pN_v9;
    }

    sig2_v9 = maxOf(0.5,  period_v9 / 8.0);
    md2_v9  = maxOf(3,    round(period_v9 * 0.40));
    if (sig2_v9 > period_v9 * 0.45) sig2_v9 = period_v9 * 0.45;

    res_v9 = detectAtSigmaFixed(proj_v9, H_v9, sig2_v9, md2_v9);
    return res_v9;
}

// ── DETECT AT ONE SIGMA (GLOBAL MIN DIST) ────────────────────
function detectAtSigma(proj, H, sigma) {
    r = detectAtSigmaFixed(proj, H, sigma, MIN_DISTANCE);
    return r;
}

// ── SPACING SCORE ─────────────────────────────────────────────
function spacingScore(peaks) {
    if (peaks[0] == -1) return 0;
    n = peaks.length;
    if (n < 3) return 0;
    sumSp = 0;
    for (i = 0; i < n - 1; i++) sumSp += peaks[i+1] - peaks[i];
    meanSp = sumSp / (n - 1);
    if (meanSp < 1) return 0;
    varSp = 0;
    for (i = 0; i < n - 1; i++) {
        d = (peaks[i+1] - peaks[i]) - meanSp;
        varSp += d * d;
    }
    stdSp = sqrt(varSp / (n - 1));
    cv    = stdSp / meanSp;
    return minOf(meanSp / 10.0, 1.0) / (1.0 + cv);
}

// ── DIAGONAL PROJECTION ──────────────────────────────────────
function buildProjection(pixels, H, W, slope, fillVal) {
    proj = newArray(H);
    for (y = 0; y < H; y++) {
        sum = 0;
        for (x = 0; x < W; x++) {
            srcY = y - round(x * slope);
            if (srcY >= 0 && srcY < H) {
                sum += pixels[srcY * W + x];
            } else {
                sum += fillVal;
            }
        }
        proj[y] = sum / W;
    }
    return proj;
}

// ── PROJECTION VARIANCE ──────────────────────────────────────
function projVariance(proj, H) {
    sm = gaussianSmooth1D(proj, SMOOTH_SIGMA);
    mean = 0;
    for (i = 0; i < H; i++) mean += sm[i];
    mean /= H;
    v = 0;
    for (i = 0; i < H; i++) {
        d = sm[i] - mean;
        v += d * d;
    }
    return v / H;
}

// Fine-sigma variance used for sign disambiguation.
// sigma=0.5 captures sharp bands that coarser sigma blurs.
function projVarianceFine(proj, H) {
    sm = gaussianSmooth1D(proj, 0.5);
    mean = 0;
    for (i = 0; i < H; i++) mean += sm[i];
    mean /= H;
    v = 0;
    for (i = 0; i < H; i++) {
        d = sm[i] - mean;
        v += d * d;
    }
    return v / H;
}

// ── LOCAL MIN / MAX FILTERS ───────────────────────────────────
function localMinFilter(arr, winSize, n) {
    halfWin = round(winSize / 2);
    result  = newArray(n);
    for (i = 0; i < n; i++) {
        r0 = maxOf(0, i - halfWin);
        r1 = minOf(n - 1, i + halfWin);
        minV = arr[r0];
        for (j = r0 + 1; j <= r1; j++) if (arr[j] < minV) minV = arr[j];
        result[i] = minV;
    }
    return result;
}

function localMaxFilter(arr, winSize, n) {
    halfWin = round(winSize / 2);
    result  = newArray(n);
    for (i = 0; i < n; i++) {
        r0 = maxOf(0, i - halfWin);
        r1 = minOf(n - 1, i + halfWin);
        maxV = arr[r0];
        for (j = r0 + 1; j <= r1; j++) if (arr[j] > maxV) maxV = arr[j];
        result[i] = maxV;
    }
    return result;
}

// ── ADAPTIVE PEAK FINDER ─────────────────────────────────────
function findPeaksAdaptive(arr, localMin, localMax, relThresh, minDist, edgeZone, H) {
    n = arr.length;
    checkList   = newArray(n + 2);
    nCheck = 0;

    if (n > 1 && arr[0] > arr[1]) { checkList[nCheck] = 0; nCheck++; }
    for (i = 1; i < n - 1; i++) {
        if (arr[i] > arr[i-1] && arr[i] >= arr[i+1]) {
            checkList[nCheck] = i; nCheck++;
        }
    }
    if (n > 1 && arr[n-1] > arr[n-2]) { checkList[nCheck] = n-1; nCheck++; }

    accepted    = newArray(nCheck);
    acceptHeights = newArray(nCheck);
    nAccepted   = 0;

    for (c = 0; c < nCheck; c++) {
        p    = checkList[c];
        pVal = arr[p];
        lMin = localMin[p];
        lMax = localMax[p];
        lRange = lMax - lMin;
        if (lRange < 0.001) continue;
        relHeight = (pVal - lMin) / lRange;
        if (relHeight < relThresh) continue;
        accepted[nAccepted]     = p;
        acceptHeights[nAccepted] = pVal;
        nAccepted++;
    }

    if (nAccepted == 0) { return newArray(0); }

    for (a = 0; a < nAccepted - 1; a++) {
        for (b = a + 1; b < nAccepted; b++) {
            if (acceptHeights[b] > acceptHeights[a]) {
                tmp = acceptHeights[a]; acceptHeights[a] = acceptHeights[b]; acceptHeights[b] = tmp;
                tmp = accepted[a];     accepted[a]     = accepted[b];     accepted[b]     = tmp;
            }
        }
    }
    kept  = newArray(nAccepted);
    nKept = 0;
    for (c = 0; c < nAccepted; c++) {
        p = accepted[c]; tooClose = false;
        for (k = 0; k < nKept; k++) {
            if (abs(kept[k] - p) < minDist) { tooClose = true; break; }
        }
        if (!tooClose) { kept[nKept] = p; nKept++; }
    }
    for (a = 0; a < nKept - 1; a++) {
        for (b = a + 1; b < nKept; b++) {
            if (kept[b] < kept[a]) { tmp = kept[a]; kept[a] = kept[b]; kept[b] = tmp; }
        }
    }
    result = newArray(nKept);
    for (i = 0; i < nKept; i++) result[i] = kept[i];
    return result;
}

// ── NORMALIZE AND INVERT ─────────────────────────────────────
function normalizeAndInvert(arr, n) {
    maxV = arr[0]; minV = arr[0];
    for (i = 1; i < n; i++) {
        if (arr[i] > maxV) maxV = arr[i];
        if (arr[i] < minV) minV = arr[i];
    }
    rng = maxV - minV;
    result = newArray(n);
    if (rng == 0) return result;
    for (i = 0; i < n; i++) result[i] = 1.0 - (arr[i] - minV) / rng;
    return result;
}

// ── GAUSSIAN SMOOTH (1-D) ─────────────────────────────────────
function gaussianSmooth1D(arr, sigma) {
    n = arr.length;
    result = newArray(n);
    if (sigma < 0.5) {
        for (i = 0; i < n; i++) result[i] = arr[i];
        return result;
    }
    radius = round(3 * sigma);
    kSize  = 2 * radius + 1;
    kernel = newArray(kSize);
    ksum   = 0;
    for (k = 0; k < kSize; k++) {
        d = k - radius;
        kernel[k] = exp(-0.5 * d * d / (sigma * sigma));
        ksum += kernel[k];
    }
    for (k = 0; k < kSize; k++) kernel[k] /= ksum;
    for (i = 0; i < n; i++) {
        v = 0;
        for (k = 0; k < kSize; k++) {
            idx = i + k - radius;
            if (idx < 0)  idx = 0;
            if (idx >= n) idx = n - 1;
            v += arr[idx] * kernel[k];
        }
        result[i] = v;
    }
    return result;
}

// ── XML METADATA READER ──────────────────────────────────────
// Looks for a PrairieView .xml file alongside the image.
// Returns array: [duration_s, scanLinePeriod_s, micronsPerPixel, lineLength_um]
// Any value that cannot be found is returned as -1.
function readXMLMeta(imagePath) {
    result = newArray(-1, -1, -1, -1);

    // Build candidate .xml path: same folder and base name, .xml extension
    dir      = File.getParent(imagePath) + File.separator;
    base     = File.getNameWithoutExtension(File.getName(imagePath));
    // Strip channel/cycle suffix: "Name_Cycle00001_Ch3_000001" -> "Name"
    // The XML sits next to the image with the scan's base name
    // Try removing common PrairieView suffixes
    xmlBase  = base;
    if (indexOf(xmlBase, "_Cycle") >= 0)
        xmlBase = substring(xmlBase, 0, indexOf(xmlBase, "_Cycle"));
    xmlPath  = dir + xmlBase + ".xml";

    if (!File.exists(xmlPath)) return result;

    xml = File.openAsString(xmlPath);
    if (xml == "") return result;

    // ── duration (framePeriod from Frame's PVStateShard) ──────
    // Pattern: inside <Frame ...><PVStateShard>...<PVStateValue key="framePeriod" value="X"/>
    // We search for the LAST framePeriod (Frame-level overrides global)
    fp = extractXMLValue(xml, "framePeriod");
    if (fp != "") result[0] = parseFloat(fp);

    // ── scanLinePeriod ────────────────────────────────────────
    slp = extractXMLValue(xml, "scanLinePeriod");
    if (slp != "") result[1] = parseFloat(slp);

    // ── micronsPerPixel (XAxis) ───────────────────────────────
    // <PVStateValue key="micronsPerPixel"><IndexedValue index="XAxis" value="X"/>
    mppIdx = indexOf(xml, "micronsPerPixel");
    if (mppIdx >= 0) {
        chunk = substring(xml, mppIdx, minOf(mppIdx + 400, lengthOf(xml)));
        xIdx  = indexOf(chunk, "XAxis");
        if (xIdx >= 0) {
            valStr = extractAttr(chunk, xIdx, "value");
            if (valStr != "") result[2] = parseFloat(valStr);
        }
    }

    // ── lineLength (pixels) → µm ─────────────────────────────
    llIdx = indexOf(xml, "lineLength=");
    if (llIdx >= 0) {
        llPx  = parseFloat(extractAttr(xml, llIdx, "lineLength"));
        if (result[2] > 0) result[3] = llPx * result[2];
    }

    return result;
}

// Helper: find last occurrence of key="..." value="..." and return value
function extractXMLValue(xml, key) {
    pattern = "key=\"" + key + "\" value=\"";
    idx = 0; found = -1;
    while (true) {
        pos = indexOf(xml, pattern, idx);
        if (pos < 0) break;
        found = pos;
        idx   = pos + 1;
    }
    if (found < 0) return "";
    start = found + lengthOf(pattern);
    end   = indexOf(xml, "\"", start);
    if (end < 0) return "";
    return substring(xml, start, end);
}

// Helper: extract an attribute value from a chunk of XML starting at pos
function extractAttr(chunk, nearPos, attrName) {
    pattern = attrName + "=\"";
    pos = indexOf(chunk, pattern, nearPos);
    if (pos < 0) pos = indexOf(chunk, pattern);   // try from beginning
    if (pos < 0) return "";
    start = pos + lengthOf(pattern);
    end   = indexOf(chunk, "\"", start);
    if (end < 0) return "";
    return substring(chunk, start, end);
}

// ── COMPUTE DERIVED METRICS ───────────────────────────────────
// Returns [flux, velocity_um_s, lineal_density, cv_intervals]
// velocity and lineal_density are -1 if metadata is unavailable.
function computeMetrics(count, duration, angleDeg, meta, peakRows, peakCount) {
    metrics = newArray(-1, -1, -1, -1);

    // Flux (RBCs/s) — always available
    if (duration > 0) metrics[0] = count / duration;

    // Velocity requires scanLinePeriod and micronsPerPixel
    scanLinePeriod = meta[1];
    micronsPerPixel = meta[2];
    if (scanLinePeriod > 0 && micronsPerPixel > 0 && angleDeg != 0) {
        tanAngle = abs(tan(angleDeg * PI / 180.0));
        if (tanAngle > 0.001) {
            // v (µm/s) = (µm/pixel) / (s/line) / tan(|angle|)
            metrics[1] = (micronsPerPixel / scanLinePeriod) / tanAngle;
        }
    }

    // Lineal density = flux / velocity  (RBCs/µm)
    if (metrics[0] > 0 && metrics[1] > 0)
        metrics[2] = metrics[0] / metrics[1];

    // Inter-RBC interval CV from peak row positions
    if (peakCount >= 3 && peakRows[0] != -1) {
        n = peakCount;
        sumSp = 0;
        for (k = 0; k < n - 1; k++) sumSp += peakRows[k+1] - peakRows[k];
        meanSp = sumSp / (n - 1);
        varSp  = 0;
        for (k = 0; k < n - 1; k++) {
            d = (peakRows[k+1] - peakRows[k]) - meanSp;
            varSp += d * d;
        }
        stdSp = sqrt(varSp / (n - 1));
        if (meanSp > 0) metrics[3] = stdSp / meanSp;
    }

    return metrics;
}

// ── DIALOGS ──────────────────────────────────────────────────
function promptForDuration(imgName) {
    Dialog.create("Scan Duration — " + imgName);
    Dialog.addMessage("No .xml metadata file found.\nPlease enter the scan duration manually.");
    Dialog.addNumber("Duration (seconds):", 1.0, 4, 8, "s");
    Dialog.show();
    return Dialog.getNumber();
}

function showResultsDialog(imgName, count, duration, angleDeg, meta, metrics) {
    flux        = metrics[0];
    velocity    = metrics[1];
    linDensity  = metrics[2];
    cv          = metrics[3];
    slp         = meta[1];
    mpp         = meta[2];
    lineLen     = meta[3];

    msg  = "Image:             " + imgName + "\n";
    msg += "─────────────────────────────────────\n";
    if (lastQCString != "OK") { msg += "RBC count:         " + count + "  [" + lastQCString + "]" + "\n"; }
    else                      { msg += "RBC count:         " + count + "\n"; }
    msg += "Duration:          " + d2s(duration, 4) + " s\n";
    msg += "Line angle:        " + d2s(angleDeg, 1) + "°\n";
    msg += "\n";
    msg += "RBC flux:          " + d2s(flux, 2) + " RBCs/s\n";
    if (velocity > 0) {
        msg += "RBC velocity:      " + d2s(velocity, 1) + " µm/s\n";
        msg += "Lineal density:    " + d2s(linDensity, 4) + " RBCs/µm\n";
    } else {
        msg += "RBC velocity:      (no .xml — enter scale manually)\n";
    }
    if (cv >= 0) {
        msg += "Inter-RBC CV:      " + d2s(cv * 100, 1) + "%\n";
    }
    if (lineLen > 0) {
        msg += "\n";
        msg += "Scan line length:  " + d2s(lineLen, 2) + " µm\n";
    }
    if (slp > 0) {
        msg += "Scan rate:         " + d2s(1/slp, 0) + " lines/s\n";
    }
    if (mpp > 0) {
        msg += "Scale:             " + d2s(mpp, 4) + " µm/pixel\n";
    }
    showMessage("RBC Linescan Results", msg);
}

function logResult(label, count, duration, angleDeg, meta, metrics) {
    flux        = metrics[0];
    velocity    = metrics[1];
    linDensity  = metrics[2];
    cv          = metrics[3];
    mpp         = meta[2];
    slp         = meta[1];

    if (!isOpen("RBC Results")) {
        run("New... ", "name=[RBC Results] type=Table");
        print("[RBC Results]",
              "\\Headings:Image\tRBC Count\tDuration (s)\tAngle (deg)\t" +
              "Flux (RBCs/s)\tVelocity (um/s)\tLineal Density (RBCs/um)\t" +
              "Inter-RBC CV\tScan Rate (lines/s)\tScale (um/px)\tQC Flag");
    }
    if (velocity   > 0)  velStr = d2s(velocity, 2);   else velStr = "N/A";
    if (linDensity > 0)  ldStr  = d2s(linDensity, 4); else ldStr  = "N/A";
    if (cv         >= 0) cvStr  = d2s(cv, 4);         else cvStr  = "N/A";
    if (slp        > 0)  srStr  = d2s(1/slp, 1);      else srStr  = "N/A";
    if (mpp        > 0)  mppStr = d2s(mpp, 6);        else mppStr = "N/A";

    plasmaStr = lastQCString;
    print("[RBC Results]",
          label          + "\t" +
          count          + "\t" +
          d2s(duration, 4) + "\t" +
          d2s(angleDeg, 1) + "\t" +
          d2s(flux, 2)   + "\t" +
          velStr         + "\t" +
          ldStr          + "\t" +
          cvStr          + "\t" +
          srStr          + "\t" +
          mppStr         + "\t" +
          plasmaStr);
}

function isImageFile(fname, exts) {
    lower = toLowerCase(fname);
    for (e = 0; e < exts.length; e++) {
        if (endsWith(lower, exts[e])) return true;
    }
    return false;
}
