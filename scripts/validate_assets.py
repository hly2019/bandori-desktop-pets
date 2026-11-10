"""Validate packaged bytes and the intentional greeting/jump variant mapping."""
from pathlib import Path
import hashlib,json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
COUNTS=[6,8,8,4,5,8,6,6,6,8,8]

def cell(image,row,col):
    return image.crop((192*col,208*row,192*(col+1),208*(row+1)))

def validate_sheet(path,expected_digest):
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==expected_digest,f'{path}: checksum differs'
    with Image.open(path) as source:
        assert source.format=='PNG' and source.mode=='RGBA',f'{path}: expected RGBA PNG'
        image=source.copy()
    assert image.size==(1536,2288),f'{path}: wrong dimensions'
    assert 0<len(raw)<=20*1024*1024,f'{path}: unexpected encoded size'
    for row,count in enumerate(COUNTS):
        for col in range(8):
            alpha=cell(image,row,col).getchannel('A')
            assert bool(alpha.getbbox())==(col<count),f'{path}: incorrect occupancy at {row},{col}'
    return image

def main():
    catalog=json.loads((ROOT/'catalog.json').read_text())
    assert len({p['slug'] for p in catalog['pets']})==len(catalog['pets'])
    for pet in catalog['pets']:
        folder=ROOT/'pets'/pet['slug'];manifest=json.loads((folder/'manifest.json').read_text())
        assert manifest['frames_per_row']==COUNTS and manifest['populated_frames']==73
        default=validate_sheet(folder/manifest['spritesheet'],manifest['sha256'])
        jump=validate_sheet(folder/manifest['jump_backup'],manifest['jump_backup_sha256'])
        for row in range(11):
            if row==4:continue
            for col in range(8):assert cell(default,row,col).tobytes()==cell(jump,row,col).tobytes(),f'{pet["slug"]}: changed non-hover cell {row},{col}'
        for col,(row,source_col) in enumerate(manifest['row_4_source_cells']):
            assert cell(default,4,col).tobytes()==cell(jump,row,source_col).tobytes(),f'{pet["slug"]}: incorrect greeting remapping'
        baselines=[]
        for col in range(5):
            bbox=cell(jump,4,col).getchannel('A').point(lambda v:255 if v>16 else 0).getbbox();baselines.append(bbox[3])
        assert max(baselines)-min(baselines)>=8,f'{pet["slug"]}: backup jump has no vertical lift'
        for name in ['greeting.gif','all-states.gif','all-states.mp4','look-loop.gif','idle-jump-idle.gif','contact-sheet.png']:
            assert (folder/'previews'/name).stat().st_size>0,f'{pet["slug"]}: missing {name}'
        print(f'{pet["slug"]}: 2 atlases, 73 frames each; hashes, transparency, greeting mapping and real jump verified')
    print('All packaged pets passed.')

if __name__=='__main__':main()
