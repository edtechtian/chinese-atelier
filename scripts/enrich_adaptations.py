"""Deterministic editorial enrichments with explicit provenance, not source changes."""
import json,re
from scripts.build_adaptations import ROOT,refs

# Chinese forms are present on the cited slide; English/pinyin/examples are editorial.
EXTRA=[
 (2,3,'曼谷','Màngǔ','Bangkok','我想先了解曼谷的几个地方。','去曼谷'),
 (2,3,'大皇宫','Dàhuánggōng','Grand Palace','请问您想先去大皇宫还是卧佛寺？','参观大皇宫'),
 (2,3,'卧佛寺','Wòfósì','Wat Pho','那儿是卧佛寺，不是大皇宫。','去卧佛寺'),
 (2,3,'安帕瓦水上市场','Ānpàwǎ Shuǐshàng Shìchǎng','Amphawa Floating Market','您想了解安帕瓦水上市场的哪一方面？','去安帕瓦水上市场'),
 (3,8,'电话卡','diànhuàkǎ','phone/SIM card','请问您说的是电话卡，还是房卡？','买电话卡'),
 (3,8,'银行卡','yínhángkǎ','bank card','房卡和银行卡不是同一种卡。','用银行卡'),
 (4,6,'门票','ménpiào','admission ticket','请问门票怎么收费？','买门票'),
 (4,6,'收费','shōufèi','to charge a fee','这个项目是否收费，需要先确认。','怎么收费'),
 (4,6,'免费','miǎnfèi','free of charge','不能因为课文写了免费，就保证今天也免费。','免费参观'),
 (5,2,'换钱','huànqián','to exchange money','我想先去银行问问怎么换钱。','去银行换钱'),
 (5,5,'泰铢','Tàizhū','Thai baht','您想用人民币换泰铢，对吗？','换泰铢'),
 (6,3,'玛雅商场','Mǎyǎ Shāngchǎng','Maya shopping centre','您想去玛雅商场，还是先了解另一个地方？','去玛雅商场'),
 (6,3,'尚泰商场','Shàngtài Shāngchǎng','Central shopping centre (source name)','请把尚泰商场和玛雅商场分别写清楚。','去尚泰商场'),
 (9,4,'泰式炒面','Tàishì chǎomiàn','Thai-style stir-fried noodles','请确认一下，是两份泰式炒面吗？','两份泰式炒面'),
 (9,7,'买单','mǎidān','to settle the bill','您好，我们想买单，请给我们看看账单。','我们买单'),
 (10,8,'登机','dēngjī','to board an aircraft','请问登机时间确认了吗？','登机时间'),
 (11,5,'巴东海滩','Bādōng Hǎitān','Patong Beach','课文里的人想在巴东海滩走走。','在巴东海滩散步'),
 (11,7,'海上摩托车','hǎishàng mótuōchē','jet ski / personal watercraft','客人不想参加海上摩托车活动，我们先了解别的选择。','海上摩托车活动'),
 (11,10,'江西冷商场','Jiāngxīlěng Shāngchǎng','Jungceylon shopping centre (source name)','您想先了解江西冷商场的哪一方面？','逛江西冷商场'),
 (12,2,'电子产品','diànzǐ chǎnpǐn','electronic products','您想买哪一种电子产品？','买电子产品'),
 (15,15,'芒果糯米饭','mángguǒ nuòmǐfàn','mango sticky rice','请确认两份芒果糯米饭。','两份芒果糯米饭'),
 (15,15,'芒果汁','mángguǒzhī','mango juice','最后的饮料改成芒果汁，对吗？','两杯芒果汁'),
 (17,11,'同事','tóngshì','colleague','我先跟负责的同事确认，再回复您。','负责的同事'),
 (18,11,'泼水节','Pōshuǐjié','Water-Splashing Festival; name used here for Songkran','课文里的泼水节活动让说话人很开心。','泼水节活动'),
 (20,14,'不要','bú yào','do not; prohibition/discouragement in these examples','请不要把一句提醒扩大成所有地方的规定。','请不要…')]
CHUNKS={'到':'到酒店了','马上':'马上到机场','等':'等一下','请':'请稍等','在':'在机场','办':'办落地签','工作':'工作人员','人员':'工作人员','给':'给我护照','方便':'太方便了','来':'来泰国','想':'想去哪儿','去':'去曼谷','还':'还想去','离':'离酒店不远','和':'和佳佳','都':'都去哪儿','要':'要办理入住','办理':'办理入住','入住':'办理入住','房间':'两个房间','一共':'一共三千泰铢','房卡':'这是你们的房卡','进来':'可以进来吗','什么':'有什么事情','事（情）':'有什么事情','行李':'您的行李','坐':'坐出租车','怎么':'怎么走','叫':'叫出租车','路边':'到路边','走':'先直走','先……,然后……':'先直走，然后左转','直':'直走','左转':'然后左转','银行':'去银行换钱','用':'用人民币换泰铢','一起':'我们一起去','从':'从这里到玛雅商场','骑':'骑摩托车','有':'有很多人','觉得':'我觉得','唱歌':'有人在唱歌','爬山':'去爬山','冷':'有点儿冷','大衣':'带一件大衣','点':'点什么菜','尝':'尝一尝','份':'两份炒面','需要':'有什么需要','做':'菜做好了吗','买':'买东西','账单':'这是您的账单','大概':'大概四个小时','上':'上飞机','逛':'逛逛商场','旁边':'海滩旁边','件':'一件衣服','合适':'不太合适','多少':'多少钱','快':'天快黑了','变':'变得热闹了','已经':'已经晚上九点了','该':'该回去了','打算':'打算什么时候去','有空儿':'你有空儿吗','怎么样':'一起去，怎么样','家':'一家饭店','推荐':'推荐的饭店','好吃':'比炸鸡好吃','庆祝':'庆祝水灯节','听说':'听说清迈的水灯节','最':'最美','飘':'天上飘着','过':'去过哪些国家','见面礼':'见面礼和中国一样吗','教':'教我合十礼','举':'手举高一点儿','活动':'有什么活动','湿':'衣服都湿了','带':'带着水枪来','像':'越来越像','表示':'表示感谢','感谢':'表示感谢','送':'送给老师','盒':'一盒巧克力','以前':'以前来过泰国吗','发现':'发现有很多寺庙','参观':'参观查龙寺','但是':'可以，但是','穿':'不要穿鞋','佛殿':'进佛殿'}
ROLE_ADDITIONS={1:'\n反思：我先确认了位置，再说明到达的时间，没有把“马上”说成“已经”。',2:'\n顾问：请问您更想了解建筑，还是看看市场生活？我们按您的兴趣排先后。',3:'\n反思：我先澄清总额，再尊重客人暂时不方便进房的选择。',4:'\n导游：您能再说一次刚才的顺序吗？如果还是不清楚，我们先确认出发点。',5:'\n工作人员：确认金额和方向以后，我们再说明最终能收到多少，不先猜测结果。',6:'\n顾问：请您再确认一下，最后需要比较的是哪两个方案？',7:'\n顾问：您可以先了解，也可以选择不尝，我会尊重您的想法。',8:'\n顾问：请问您希望怎样安排休息？确认条件以后再一起决定。',10:'\n协调人：我会把日期、出发和登机分别列出来，请您再核对一次。',11:'\n顾问：请问您今天有多少时间？我们按您的兴趣安排下一步。',12:'\n店员：请您再核对数量，确认清楚以后再决定是否购买。',13:'\n同伴乙：好的，我们确认一下见面的地点和联系办法，最后再各自出发。',14:'\n甲：好的，这只是建议，我们等信息确认以后再一起决定具体安排。',15:'\n甲：我再复述一次最后的饮料和份数，请大家看看有没有需要修改的。',16:'\n讲解员：您也可以先了解材料，暂时不决定怎样参加。',17:'\n接待人：请问您还有什么想了解的地方？我们可以先确认称呼，再继续交流。',18:'\n顾问：最后请大家分别确认自己的选择，不用为了跟别人一样而勉强答应。',20:'\n导游：谢谢您说明情况，我们先等工作人员确认，再决定下一步。'}

def enrich(specs):
 for spec in specs:
  n=int(spec['id'].split('-')[1]);
  for slide,prompts in spec['readingPrompts'].items():
   for i,prompt in enumerate(prompts):prompt.update({'id':f'zt-{n:02d}-discussion-{slide}-{i+1}','origin':'supplementary','sourceRefs':refs(n,int(slide))})
  for decision in spec['pedagogy']['decisions']:decision.update({'id':f'zt-{n:02d}-decision-'+decision['action'],'origin':'adaptation'})
  spec['liveListening']={'id':f'zt-{n:02d}-live-listening','origin':'supplementary','sourceRefs':refs(n,*spec['readingSlides']),'instructions':['Work with a partner or teacher; no recording is supplied or captured. Listener closes the Reading section.','Partner reads the first original dialogue twice, without adding facts. First listen for the purpose; then note details.','Listener answers the focus question below and asks one clarification in Chinese. Reopen Reading to compare against the source. Swap roles.'],'focus':spec['questions'][0]['prompt'],'questionId':spec['questions'][0]['id'],'assessment':'Teacher checks comprehension and response to clarification from live evidence. Reading fluency does not substitute for listening evidence.'}
  for t in spec['tasks']:
   if t['type']=='roleplay' and n in ROLE_ADDITIONS:t['model']+=ROLE_ADDITIONS[n]
   t['modelScope']='Example exchange and reflection' if t['type']=='roleplay' else 'One possible complete response'
  if n==1:
   spec['tasks'][0]['model']+='两人所在的阶段不同。';spec['tasks'][1]['model']+='谢谢您的配合。'
  if n==3:
   spec['tasks'][0]['model']='对话确认两个房间的费用“一共是3,000泰铢”，并提到房卡。“一共”说明这是总额，不能直接当作每间房每晚的价格。不过，课文没有说明入住晚数和房型。工作人员应先核对预订，再向客人确认这些未说明的细节。'
   spec['tasks'][2]['model']=spec['tasks'][2]['model'].replace('在这次培训情境中，','按照这里确认的预订，').replace('练习情境为两个房间','已确认两个房间');spec['tasks'][2]['model']+='请您核对上述信息，谢谢配合。'
   old=spec['questions'][-1]
   old.update({'id':'zt-03-q-arrival-contrast','prompt':'Which line highlights a new arrival rather than simply a location?','options':[{'id':'o1','text':'我们到酒店了。'},{'id':'o2','text':'我们在酒店。'},{'id':'o3','text':'这是酒店。'}],'answer':'o1','explanation':'到酒店了 reports arrival; 在酒店 reports location. Both can be grammatical but serve different purposes.','sourceRefs':refs(3,5,12),'category':'grammar'})
  if n==13:spec['tasks'][0]['model']+='双方仍保持合作。'
  if n==18:spec['patterns'][0]['sourceRefs']=refs(18,2,13)
 return specs

def enrich_vocabulary(app):
 for l in app['lessons']:
  for v in l['vocabulary']:
   chunk=CHUNKS.get(v['chinese'])
   if chunk:v['collocations']=[chunk];v['collocationOrigin']='supplementary';v['collocationNote']='Editorial usage chunk; not an additional textbook quotation.'
   if v['chinese']=='事（情）':v.update({'example':'小乐：请进，有什么事情?','exampleOrigin':'textbook','exampleSourceRefs':refs(3,11)})
   if v['chinese']=='先……,然后……':v.update({'example':'先直走,然后左转。','exampleOrigin':'textbook','exampleSourceRefs':refs(4,5)})
  for idx,(n,slide,ch,py,en,example,chunk) in enumerate(EXTRA):
   if n!=l['number'] or any(v['chinese']==ch for v in l['vocabulary']):continue
   l['vocabulary'].append({'id':f'zt-{n:02d}-expression-{idx+1:02d}','chinese':ch,'pinyin':py,'meaning':en,'example':example,'exampleOrigin':'supplementary','exampleSourceRefs':[],'collocations':[chunk],'collocationOrigin':'supplementary','gloss':{},'origin':'adaptation','sourceRefs':refs(n,slide),'pinyinOrigin':'adaptation','editorialNote':'Chinese expression from the cited source; pinyin, English, context sentence and chunk are newly authored editorial support.'})
 return app
