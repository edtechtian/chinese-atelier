"""Prefer visually checked original PPT images for source vocabulary cards.

This is an editorial mapping, not additional textbook content. Abstract words and
objects without a verified picture remain text-only. Existing visual activity IDs
and their saved results are preserved.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DESCRIPTIONS={
 1:'An original PPT illustration of travellers with luggage in an airport waiting area.',
 7:'A photograph of a hotel building and swimming pool from the original PPT.',
 20:'A pineapple with sliced fruit, used as an example of fruit; not a picture of every fruit.',
 24:'An original PPT illustration of a hiker with a backpack facing mountain scenery.',
 45:'Sky lanterns floating into a dark sky in an original PPT image.',
}
WORD_IMAGES={'机场':1,'酒店':7,'房间':5,'大皇宫':4,'嘟嘟车':15,
 '寺庙':18,'夜市':19,'水果':20,'爬山':24,'面':26,'泰式炒面':26,
 '沙滩':31,'咖啡店':40,'炸鸡':42,'青木瓜沙拉':41,'水灯':44,
 '水灯节':43,'孔明灯':45,'合十':47}
def apply_source_vocabulary_images(data,curriculum):
 candidates=json.loads((ROOT/'curriculum/visual_source_candidates.json').read_text())
 for number,description in DESCRIPTIONS.items():
  row=candidates[number];key='source-'+str(number)
  data['images'][key]={'id':key,'src':row['url'],'alt':description,
   'kind':'source_illustration' if number in {1,24} else 'source_photo',
   'origin':'textbook_asset','sourceRefs':[row['lesson']+'-slide-'+str(row['slide']).zfill(3)],
   'attribution':'Original supplied 《走遍泰国》 PPT · Prince of Songkla University Phuket Confucius Institute. Embedded third-party rights are not independently cleared.',
   'status':'visible_features_checked_pending_teacher'}
  image=data['images'][key];original=ROOT/'public'/image['src'].lstrip('/')
  for width in [480,960]:
   relative='/assets/visual/'+key+'-'+str(width)+'.webp';target=ROOT/'public'/relative.lstrip('/')
   if not target.exists() and original.is_file():
    from PIL import Image,ImageOps
    with Image.open(original) as picture:
     picture=ImageOps.exif_transpose(picture).convert('RGB');picture.thumbnail((width,width))
     picture.save(target,'WEBP',quality=84)
   if target.is_file():image.setdefault('responsive',{})[str(width)]=relative
 words={v['id']:v for lesson in curriculum['lessons'] for v in lesson['vocabulary']}
 for unit in data['units']:
  for mapping in unit['vocabulary']:
   word=words[mapping['itemId']];number=WORD_IMAGES.get(word['chinese'])
   mapping['imageId']='source-'+str(number) if number is not None else None
   mapping['status']='ppt_image_pending_teacher' if number is not None else 'text_only_no_verified_ppt_image'
   mapping['reason']=None if number is not None else 'No visually verified matching PPT picture. Review the word and its source sentence without an unrelated illustration.'
   mapping['imageSourceRefs']=data['images'][mapping['imageId']]['sourceRefs'] if number is not None else []
  # Existing supplementary picture activities keep their IDs; use the original
  # image wherever the same concrete expression has a checked PPT counterpart.
  for activity in unit['activities']:
   word=words.get(activity.get('vocabularyId'));number=WORD_IMAGES.get(word['chinese']) if word else None
   if number is not None:activity['imageId']='source-'+str(number)
   if activity['type']=='picture_match':
    for pair,word_id in zip(activity['pairs'],activity['answer']):
     number=WORD_IMAGES.get(words[word_id]['chinese'])
     if number is not None:pair['imageId']='source-'+str(number)
 return data
if __name__=='__main__':
 path=ROOT/'curriculum/visual_learning.json'
 data=apply_source_vocabulary_images(json.loads(path.read_text()),json.loads((ROOT/'data/curriculum.json').read_text()))
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 mapped=sum(bool(v['imageId']) for u in data['units'] for v in u['vocabulary'])
 print(f'{mapped}/268 vocabulary records use original PPT images; the rest are text-only.')
