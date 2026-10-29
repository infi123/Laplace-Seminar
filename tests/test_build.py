import json
import unittest
from pathlib import Path
from build_all import frame_manifest, assert_assets, html_document

ROOT=Path(__file__).resolve().parents[1]

class BuildTests(unittest.TestCase):
    def test_frame_count_and_mapping(self):
        text=(ROOT/'main.tex').read_text(encoding='utf-8')
        count,mapped=frame_manifest(text)
        self.assertGreaterEqual(count,6)
        essential={'euler_decay','complex_modes','time_shift','dirac_pulse','convolution','system_response'}
        self.assertTrue(essential.issubset(set(mapped)))
        self.assertEqual(len({v['slide'] for v in mapped.values()}),len(mapped))

    def test_inserted_slide_keeps_animation_attached(self):
        tex=(ROOT/'main.tex').read_text(encoding='utf-8')
        count_before,before=frame_manifest(tex)
        extra='\\begin{frame}{שקף בדיקה}תוכן\\end{frame}\n'
        # Insert one new frame after document start, not within an animated frame.
        updated=tex.replace('\\begin{document}', '\\begin{document}\n'+extra, 1)
        count_after,after=frame_manifest(updated)
        self.assertEqual(count_after,count_before+1)
        self.assertEqual(set(after),set(before))
        for k in before:self.assertEqual(after[k]['slide'],before[k]['slide']+1)

    def test_manifest_unique(self):
        cfg,count,mapped=assert_assets()
        self.assertEqual(set(cfg['animations']),set(mapped))

    def test_html_has_no_video_overlays(self):
        result=html_document([],{},False)
        self.assertIn('object-fit:contain',result)
        self.assertNotIn('class="overlay"',result)
        self.assertIn('video',result)

if __name__=='__main__':unittest.main()
