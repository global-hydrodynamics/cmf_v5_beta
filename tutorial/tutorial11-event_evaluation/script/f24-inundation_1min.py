#!/usr/bin/env python3
"""Render only the existing preliminary Step24 simulated-depth product."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from netCDF4 import Dataset
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tutorial-dir",type=Path,required=True)
    a=p.parse_args();t=a.tutorial_dir
    report=json.loads((t/"metadata/24_downscaling_verification.json").read_text())
    with Dataset(t/report["output"]) as d:
        depth=np.ma.asarray(d["flddph"][:]);lon=d["lon"][:];lat=d["lat"][:]
    west,south,east,north=report["extent_west_south_east_north"]
    fig,ax=plt.subplots(figsize=(8.4,7.2))
    fig.subplots_adjust(left=.1,right=.88,bottom=.22,top=.87)
    ax.set_facecolor("#b8b8b8")
    extent=[west,east,south,north]
    dry=np.ma.masked_where(np.ma.getmaskarray(depth)|(depth.filled(-1)!=0),np.ones(depth.shape))
    ax.imshow(dry,extent=extent,origin="upper",interpolation="none",cmap=ListedColormap(["#f3efe2"]),vmin=0,vmax=1)
    wet=np.ma.masked_where(depth.filled(-1)<=0,depth)
    image=ax.imshow(wet,extent=extent,origin="upper",interpolation="none",cmap="YlGnBu",vmin=0,vmax=10)
    ax.set_aspect(1/np.cos(np.deg2rad((south+north)/2)))
    ax.set_xlim(west,east);ax.set_ylim(south,north)
    ax.set_xlabel("Longitude (°E)");ax.set_ylabel("Latitude (°N)")
    ax.set_xticks(np.arange(west,east+.1,1));ax.set_yticks(np.arange(south,north+.1,1))
    fig.colorbar(image,ax=ax,shrink=.78,pad=.035,extend="max",label="Simulated inundation depth (m)")
    ax.legend(handles=[Patch(facecolor="#f3efe2",label="Dry (0 m)"),Patch(facecolor="#b8b8b8",label="NoData / unmapped")],loc="lower left",fontsize=8,framealpha=.95)
    fig.suptitle("Tutorial 11 Fig. 24 — Preliminary 1 arcmin inundation",fontsize=13,y=.96)
    ax.set_title("S1A orbit 038784 · 15 July 2021\nObservation ≈05:50:40 UTC → model 06:00 UTC (+9 min 20 s)",fontsize=10)
    fig.text(.1,.12,"Tributary-aware CaMa-Flood downscaling of flddph; Rhine2021.\nPermanent-water minimum: 0.1 m. Positive depth includes river water.\nPreliminary simulated product; no satellite comparison or accuracy assessment.",fontsize=9,va="top")
    output=t/"figure/f24-inundation_1min.png";output.parent.mkdir(exist_ok=True)
    fig.savefig(output,dpi=200);plt.close(fig);print(output)


if __name__=="__main__":main()
