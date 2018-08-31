#encoding:utf-8
import string, time, numpy as np
from icalendar import Calendar, Event, LocalTimezone, vDatetime
from datetime import datetime, timedelta, time
from dateutil import rrule
from numpy import floor,ceil
import lxml.etree as etree
import qrcode, re

import os,sys

# Списки ключевых слов, регулярные выражения -- для присвоения тегов
course_list = [ u'уирс', u'бола', u'спецтех1', u'мсс', u'ипк', u'пиивк', u'алгивк', u'цс сула', u'цс ивк', u'мио ивк']
sem_start_re = re.compile( u'начало семестра: [0-9.]+' )
sem_finish_re = re.compile( u'конец семестра: [0-9.]+' )

prof_list_303 = sorted([ u'Белобжеский', u'Гуреев', u'Захарян', u'Костюков', u'Капырин', u'Новичков', u'Нгуен', u'Соболев', u'Сурков', u'Ушаков', u'Мишин']) # u'Мингалиев',
prof_shorter_303 = sorted([ u'Белоб-\nжеский', u'Гуреев', u'Захарян', u'Костюков', u'Капырин', u'Новичков', u'Нгуен', u'Соболев', u'Сурков', u'Ушаков', u'Мишин']) # u'Минга-\nлиев',
prof_longer_303 = sorted([ u'Белобжеский Л.А.', u'Гуреев В.О.', u'Захарян Р.Р.', u'Костюков В.М.', u'Капырин Н.И.', u'Новичков В.М.', u'Нгуен Н.М.', u'Соболев В.И.', u'Сурков Д.А.', u'Ушаков А.Н.', u'Мишин Ю.Н.'])

prof_list_305    = sorted([ u'Афонин', u'Пронькин', u'Бережной', u'Антонов', u'Корягин', u'Мельников', u'Веремеенко', u'Жарков', u'Плеханов', u'Кузнецов', u'Кошелев'])
prof_shorter_305 = sorted([ u'Афонин', u'Пронькин', u'Бережной', u'Антонов', u'Корягин', u'Мельников', u'Веремеенко', u'Жарков', u'Плеханов', u'Кузнецов', u'Кошелев'])
prof_longer_305  = sorted([ u'Афонин А.А.', u'Пронькин А.Н.', u'Пронькин Д.В.', u'Антонов Д.А.', u'Корягин Л.И.', u'Мельников В.Е.', u'Веремеенко К.К.', u'Жарков М.В.', u'Плеханов В.Е.', u'Кузнецов И.М.', u'Кошелев Б.В.'])

prof_list = sorted( prof_list_303 + prof_list_305 )
all_prof_list = sorted( prof_list_303 + prof_list_305 )
prof_shorter = sorted( prof_shorter_303 + prof_shorter_305 )
prof_longer = sorted( prof_longer_303 + prof_longer_305 )

group_re1 = re.compile( u'[1-9,З][O,О,З,0,о,з][0-9]{3}[CСБМсбкиКИ]+' ) # 3О505С
group_re2 = re.compile( u'[0-9]*[МТ]*[1-9,З]+[O,О,З,0,о,з,В,в]-[0-9]{3}[CСБМсбкиКИ]+-[0-9]{2}' ) # 3О-405С-14, М5В-105Мк-17, Т11О-202Б-17, Т1О-302Б-16, 1ТСБ-4ДБ-041-15
group_re3 = re.compile( u'[0-9]*[МТ]*[1-9,З,С]+[O,О,З,0,о,з,В,в,Б]-[0-9]ДБ-[0-9]{3}[CСБМсбкиКИ]*-[0-9]{2}' ) # 3О-405С-14, М5В-105Мк-17, Т11О-202Б-17, Т1О-302Б-16, 1ТСБ-4ДБ-041-15, 1ТСБ-4ДБ-041-15

#group_re = re.compile( u'[M,C,O,М,С,О][1-9,З][O,О,З,0,о,з][0-9]{3}[CСБМсбкиКИ]+' ) # M3О505С
time_re = re.compile(  u'[0-9]{1,2}:[0-9]{1,2}' )                     # 0:00   99:99
week_span_re = [ re.compile( u'нед[0-9,]+$' ), \
                 re.compile( u'нед[0-9]+-[0-9]+' ), \
                 re.compile( u'до[0-9]+-[0-9]+нед' ), \
                 re.compile( u'с[0-9]+нед' ), \
                 re.compile( u'до[0-9]+нед' ) ]
date_span1 = re.compile( u'[сc][0-9]{1,2}.[0-9]{1,2}по[0-9]{1,2}.[0-9]{1,2}' ) # с 00.00 по 00.00
date_span2 = re.compile( u'с[0-9]{1,2}.[0-9]{1,2}' )                           # с 00.00
date_span3 = re.compile( u'[пд]о[0-9]{1,2}.[0-9]{1,2}' )                       # по 00.00   до   00.00
fio_marks = [ re.compile( u'проф[. ]+' ), \
              re.compile( u'доц[. ]+' ), \
              re.compile( u'ст[. ]+пр[. ]+' ), \
              re.compile( u'асс[. ]+' ), \
              re.compile( u'[А-Яа-я]+ [А-Я]+\.[А-Я]\.' ), \
              re.compile( u'[А-Я]+\.[А-Я]\.[ ]*[А-Яа-я]+' ) ]
group_span = re.compile( u'[0-9]к[0-9]ф[сб]?' )
group_marker1 = re.compile( u'[0-9]к[0-9]ф[CСБсбМм]?$' )
group_marker2 = re.compile( u'[1-9,З][O,О,З,0,о,з][0-9]{3}[CСБМсбкиКИ]+$' )
month_names = [ u'янв', u'фев', u'мар', u'апр', u'мая', u'июн', u'июл', u'авг', u'сен', u'окт', u'ноя', u'дек' ]

from matplotlib import cm
cmap = cm.get_cmap('tab20') # Pastel1, Spectral, hsv, Pastel1, gist_rainbow
prof_colors = {'':'rgb(255, 255, 255)'}
for i,prof in enumerate(sorted(prof_list)):
    prof_colors[prof] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i) / (len(prof_list)-1) )[0:3] ]) + ')' # colors[i % len(colors)]

room_colors = {'':'white'}
course_colors = {'':'white'}
groups_colors = {'':'white'}

time_spans = [ time(9,0,0), time(10,45,0), time(13,0,0), time(14,45,0), time(16,30,0), time(18,15,0), time(20,00,0) ]
lab_timespans = [ time(9,0,0), time(13,0,0), time(16,30,0) ]

wday1 = [u'понедельник', u'пн', u'пон']
wday2 = [u'вторник', u'вт', u'вто']
wday3 = [u'среда', u'ср', u'сре']
wday4 = [u'четверг', u'чт', u'чг', u'чет']
wday5 = [u'пятница', u'пя', u'пт', u'пят']
wday6 = [u'суббота', u'сб', u'су', u'суб']
wday7 = [u'воскресенье', u'вс', u'во', u'вос']
wday_list = wday1 + wday2 + wday3 + wday4 + wday5 + wday6 + wday7
wday_color = ['#dddddd' for nw in wday_list]

#cmap = cm.get_cmap('Pastel1') # Spectral, hsv, Paired, gist_rainbow, Spectral
#cmap = cm.get_cmap('hsv')
#for i,nw in enumerate(wday_list):
#    wday_color[i] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i)/(len(wday_list)) )[0:3] ]) + ')'

wdays_long = [u'Понедельник', u'Вторник', u'Среда', u'Четверг', u'Пятница', u'Суббота', u'Воскресенье']
wdays = [u'Пн', u'Вт', u'Ср', u'Чт', u'Пт', u'Сб', u'Вс']

class_type_lab = [ u'лб', u'ЛБ', u'лаб', u'лабораторная', u'лабораторная работа', u'лабораторные', u'лабораторные работы']
class_type_lec = [ u'лекция', u'лз', u'ЛК', u'лекции' ]
class_type_pract = [ u'практика', u'пз', u'ПЗ', u'практическое занятие', u'практические занятия' ]
class_type = class_type_lab + class_type_lec + class_type_pract
ct_marker_LAB = u'ЛБ'; ct_marker_LK = u'ЛК'; ct_marker_PZ = u'ПЗ';

even_week_list = [u'н.н.', u'нн', u'нижниенедели', u'нижняянеделя']
odd_week_list  = [u'в.н.', u'вн', u'верхниенедели', u'верхняянеделя']
week_span_list = even_week_list + odd_week_list

holidays = [ '23.02', '08.03', '01.05', '09.05', '12.06', '04.11' ]

sem_start = datetime( year=2018, month=9, day=1 )
sem_finish = datetime( year=2018, month=12, day=29)

# Сократить временную метку
def s_time( s ):
    s_nb = u'⁰¹²³⁴⁵⁶⁷⁸⁹'
    s_out = s;
    for i,j in enumerate(s_nb):
        s_out = s_out.replace( str(i), j )
    return s_out

# Сделать список групп из сокращённого обозначения (пока, только очные группы)
def courseId2groupName( s ): # 2к3фБ/3 -> 3О207Б, ...
  s1 = s.split('/'); year = s1[0][0]; fac = s1[0][2]; gr_type = s1[0][4:]
  if len(s1)>1: gnum = s1[1]
  else: gnum = '0'
  s2 = fac + u'О' + year + '%02d' % int(gnum) + gr_type
  return s2

# Вернуть название набора групп -- либо сокращённое обозначение, либо просто первую в списке
def short_group_name( s ):
  # Простой вариант
  p = u''
  if s.count(',')>0 or s.count(' ')>0: p = u'…'
  compiled = s.replace('(',' ').replace(',',' ').split(' ')[0]
  if '-' in compiled: compiled = compiled.split(u'-')[1]
  return compiled + p

# Вернуть сокращённое название кабинета
def short_room_name( s ):
  if u'(Орш' in s: return s.split(u'(Орш')[0]
  return s

# Вернуть в качестве описания тега -- список групп, сгенерированный из укороченного описания
def groupstring2list( s ):
  l = []
  mem = ''
  # '2к3фБ' (3,4) ->  
  # '2к3фБ (7-10)' -> 
  # '4к3фБ (7,9,10,11)' -> 
  for t in s.replace(' ','').replace('(',',').replace(')','').replace(u'C',u'С').replace(u'c',u'с').split(','):
      if t == '': continue
      elif group_marker2.match(t): mem = ''; l.append(t);
      elif group_marker1.match(t): mem = t;
      elif '-' in t:
          num1, num2 = t.split('-')
          for c in range( int(num1), int(num2)+1):
              l.append( courseId2groupName(mem + '/' + str(c)) )
      else: l.append( courseId2groupName(mem + '/' + t) )
  return l

# Вернуть список из номеров недель, исходя из тега
def weekspan2list( s ):   # н.н. | недели 3,5,7,9,11,13,15 | нед. 4,6,8,10
  l = [ int(x) for x in range(1,18) ]
  if s in even_week_list:  l = [2,4,6,8,10,12,14,16,18];
  elif s in odd_week_list: l = [1,3,5,7,9,11,13,15,17];
  else:
      s = s.replace( u'недели', u'нед' )
      if (s[0] in [u'c',u'с']) and s[-3:] == u'нед':
          num = s[1:-3];
          l = [ int(c) for c in range( int(num), 18) ]
      elif (s[0:2] == u'до') and s[-3:] == u'нед':
          num = s[2:-3];
          l = [ int(c) for c in range( 1, int(num)) ]
      elif s[0:3] == u'нед':
          if '-' in s:
              num1, num2 = s[3:].split(u'-')
              l = [ int(c) for c in range( int(num1), int(num2)+1) ]
          else: l = [int(x) for x in s[3:].split(',')]
      else: l = s.split(',')
  return l

# Определить, какие недели встречаются в списке -- верхние (up), нижние (dn) или обе (updn)
def get_up_down_list( weeks_list ):
  ud = ''
  for i in [1,3,5,7,9,11,13,15,17]:
      if i in weeks_list: ud += 'up'; break;
  for i in [2,4,6,8,10,12,14,16,18]:
      if i in weeks_list: ud += 'dn'; break;
  return ud

# Присвоение тэга изучаемой записи
def tag_me( s ):
  tag = ''
  if s in prof_list: tag = ('prof', s);
  elif s.lower() in course_list: tag = ('course', s)
  elif s.lower() in wday_list: 
      if s.lower() in wday1: tag = ('wday', 0)
      elif s.lower() in wday2: tag = ('wday', 1)
      elif s.lower() in wday3: tag = ('wday', 2)
      elif s.lower() in wday4: tag = ('wday', 3)
      elif s.lower() in wday5: tag = ('wday', 4)
      elif s.lower() in wday6: tag = ('wday', 5)
      elif s.lower() in wday7: tag = ('wday', 6)
  elif group_re3.match(s.split(',')[0]): tag = ('group', ( s.split(',') ))
  elif group_re1.match(s) or group_re2.match(s): tag = ('group', [s])
  elif ',' in s and group_re2.match(s.split(',')[0]): tag = ('group_list', ( s.split(',') ))
  elif group_span.match( s.lower() ): tag = ('group_list', groupstring2list( s ))

  #if group_re.match(s) : tag = ('group_list', s )
  elif time_re.match(s): tag = ('time', timedelta( hours=int(s.split(':')[0]), minutes=int(s.split(':')[1]) ) )
  elif s.lower().replace('.','') in class_type:
      if s.lower().replace('.','') in class_type_lab: tag = ('class_type', ct_marker_LAB )
      elif s.lower().replace('.','') in class_type_lec: tag = ('class_type', ct_marker_LK )
      elif s.lower().replace('.','') in class_type_pract: tag = ('class_type', ct_marker_PZ )

  if tag == '':
    for w in week_span_re:
      if w.match( s.replace(u'недели',u'нед').replace(u'.',u'').replace(u' ','') ):
        tag = ( 'week_span', weekspan2list(s.replace(' ','').replace('.','')) )
  
  if tag == '':
    if s.lower().replace(' ','') in week_span_list : tag = ( 'week_span', weekspan2list(s.replace(' ','').replace('.','')) )
    if date_span1.match( s.replace(' ','') ) or \
       date_span2.match( s.replace(' ','') ) or \
       date_span3.match( s.replace(' ','') ):
         tag = ('date_span', s)
    for r in fio_marks:
      if r.match( s ): tag = ('prof', s)

    if sem_start_re.match( s.lower() ): tag = ('sem_start', s)
    if sem_finish_re.match( s.lower() ): tag = ('sem_finish', s)

  if tag == '': 
      ndigits = sum(c.isdigit() for c in s)
      if ndigits >= 0.3 * float(len(s)) or u'каф.' in s: tag = ('location', s)  # Более 30% цифр -- это название аудитории
      else: tag = ('course', s) # Это название предмета
  return tag






#########################################################################
# Процедура отрисовки индивидуальных листов преподавателей/комнат/групп #
#########################################################################

def draw_prof_room( cal, selected_prof='', selected_room='', selected_group = '', color_by_course = 0, \
                    color_by_room=0, color_by_prof=0, f_name = 'sample' ):
    weekday_stripes = [ [list()], [list()], [list()], [list()], [list()], [list()] ] # Без воскресенья
    for component in cal.walk():
        if component.name == "VEVENT":

            # Начало и конец [события]
            #st = component.get('date_time_start')
            st = datetime.strptime( component.get('date_time_start'), '%Y-%m-%d %H:%M:%S');
            #ft = component.get('date_time_end')
            ft = datetime.strptime( component.get('date_time_end'), '%Y-%m-%d %H:%M:%S');
            prof = component.get('prof')
            loc = component.get('location')
            groups = component.get('groups').split(' ')
            wd = st.weekday()
            component['st'] = st
            component['ft'] = ft

            rrset = rrule.rruleset()
            rrset.rrule( rrule.rrulestr( component.get('rrule').to_ical(), dtstart = st ) )
            for evt in list(rrset):
                if evt > sem_finish: continue;

                st = evt;
                ft = evt + (ft-st);

                # Первый пункт -- чтобы не рисовать расписания, заданные группам, для преподавателей других кафедр
                if ( selected_room == '' and selected_prof == '' and selected_group == '' and prof in prof_list) or \
                   ( selected_room != '' and selected_room in loc ) or \
                   ( selected_group != '' and selected_group in groups ) or \
                   ( selected_prof != '' and selected_prof in prof ):
                    
                    # Найти следующую свободную полоску в дне недели, куда можно вписать [событие]
                    free_stripe = -1
                    for i,stripe in enumerate( weekday_stripes[wd] ):
                        found = 0;
                        for e in stripe:
                        	if (st <= e['st'] < ft) or (st < e['ft'] < ft): found = 1; break;
                        if found == 0: free_stripe = i; break; # Нашли полоску куда можно разместить событие
                    if free_stripe == -1:
                        weekday_stripes[wd].append( list() ); free_stripe = len( weekday_stripes[wd] ) - 1;
                
                    # Разместить [событие] на свободной полоске
                    weekday_stripes[wd][free_stripe].append( component )
    
    # Вспомогательные числа
    nb_of_stripes = sum( [len(x) for x in weekday_stripes] )
    week_starts_of_sem = sorted( set( e['st'] - timedelta( days=e['st'].weekday(), hours=e['st'].hour, minutes=e['st'].minute, seconds=e['st'].second ) for e in cal.walk() if e.name == "VEVENT" ))
    nb_weeks_in_sem = len( week_starts_of_sem )
    nb_stripes_in_wday = [ len(x) for x in weekday_stripes ]
    time_blocks_of_sem = set( e['st'] for e in cal.walk() if e.name == "VEVENT" )
    # csv_code was here

    nb_columns = nb_of_stripes
    nb_rows = nb_weeks_in_sem * (len( time_spans )+1)

    col_w = 46; row_h = 30; rxy = 0; col_space = 2; row_space = 2; col_skip  = 30; row_skip  = 20
    top_space = 100; left_space = 200
    
    doc_w = nb_columns * col_w  +  left_space  +  col_skip*5                    +  (nb_columns - 2)*col_space
    doc_h = nb_rows * row_h     +  top_space   +  row_skip*(nb_weeks_in_sem-2)  +  (nb_rows    - 2)*row_space
    
    txt_style_0  = 'font-family:Sans;font-size:6px;text-anchor:middle;dominant-baseline:top'  # Надписи на блоках
    txt_style_0b = txt_style_0 + ';font-weight:bold'
    txt_style_1  = 'font-family:Sans;font-size:30px;text-anchor:middle;dominant-baseline:top' # Дни недели
    txt_style_2  = 'font-family:Sans;font-size:16px;text-anchor:middle;dominant-baseline:top' # Блоки описания недели
    txt_style_3  = 'font-family:Sans;font-size:48px;text-anchor:middle;dominant-baseline:top' # Номера недель
    
    doc = etree.Element('svg', width=str(doc_w), height=str(doc_h), version='1.1', xmlns='http://www.w3.org/2000/svg')    
    
    # Белый фон
    etree.SubElement( doc, 'rect', x=str(0), y=str(0), width=str(doc_w), height=str(doc_h), fill="white")
    
    # Названия дней недели
    for nb_wday,wday in enumerate(weekday_stripes):
        nb_stripes_before_n = ( sum( [len(weekday_stripes[i]) for i in range(0,nb_wday)] ))
        nb_stripes_now      = len( weekday_stripes[nb_wday] )
        w = nb_stripes_now * col_w  +  (nb_stripes_now-1) * col_space
        x = left_space  +  nb_wday*col_skip  +  (nb_stripes_before_n - 1) * col_space  +  nb_stripes_before_n * col_w
        y = 0 #top_space   -  3*row_h
        etree.SubElement( doc, 'rect', x=str(x), y=str(0), width=str(w), height=str(doc_h), rx=str(rxy), ry=str(rxy), fill="rgba(220,220,220,0.5)", style="fill:#000000;fill-opacity:0.08" )
        etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(w), height=str(2*row_h), rx=str(rxy), ry=str(rxy), stroke="black", fill='white')
        tx = etree.Element( 'text', x=str(x + w/2), y=str(y + row_h + 14), fill='black', style=txt_style_1 )
        tx.text = wdays[nb_wday];
        doc.append( tx )
    
    # Номера недель
    for nb_week,wstart in enumerate( sorted(week_starts_of_sem) ):
        nb_spans_before = ( ((len(time_spans) + 1) * nb_week ) ) #+ nb_timeslot )
        nb_spans_now    = len(time_spans) 
    
        h = nb_spans_now * row_h  +  (nb_spans_now-1) * row_space
        w = 3*float(left_space)/5  -  row_skip
        x = 0
        y = top_space  +  nb_week*row_skip  +  (nb_spans_before-1) * row_space + nb_spans_before * row_h
    
        etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(doc_w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill="rgba(220,220,220,0.5)", style="fill:#000000;fill-opacity:0.08" )
        etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill='white')
    
        wsd = wstart.date();                        ws = u'%d %s' % (wsd.day, month_names[wsd.month-1])
        wed = (wstart + timedelta(days=6) ).date(); we = u'%d %s' % (wed.day, month_names[wed.month-1])
        
        tx = etree.Element( 'text', x=str(x + w/2), y=str(y + h/2 - 64 + 3), fill='black', style=txt_style_2 );  tx.text = ws; doc.append( tx )
        tx = etree.Element( 'text', x=str(x + w/2), y=str(y + h/2 - 24), fill='black', style=txt_style_2 ); tx.text = u'Неделя'; doc.append( tx )
        tx = etree.Element( 'text', x=str(x + w/2), y=str(y + h/2 + 24),  fill='black', style=txt_style_3 ); tx.text = str(nb_week+1); doc.append( tx )
        tx = etree.Element( 'text', x=str(x + w/2), y=str(y + h/2 + 64 + 3), fill='black', style=txt_style_2 ); tx.text = we; doc.append( tx )
        
        # Временные отрезки
        for nb_timeslot,timeslot in enumerate( time_spans ):
            d_slot = nb_timeslot * row_h  +  nb_timeslot * row_space
            w = 2*left_space / 5  -  row_skip
            x = 3*left_space/5
            y1 = y + d_slot
            etree.SubElement( doc, 'rect', x=str(x), y=str(y1), width=str(w), height=str(row_h), rx=str(rxy), ry=str(rxy), stroke="black", fill='white')
            tx = etree.Element( 'text', x=str(x + w/2), y=str(y1 + row_h/2 + 8), fill='black', style=txt_style_2 );  tx.text = u'%d:%02d' %(timeslot.hour, timeslot.minute);
            doc.append( tx )
    
    # Блоки занятий
    for nb_wday,wday in enumerate(weekday_stripes):
        for nb_stripe,stripe in enumerate(wday):
            for e in stripe:
                for nb_week,wstart in enumerate( sorted(week_starts_of_sem) ):
                    for nb_timeslot,timeslot in enumerate( time_spans ):
                        datetime_slot = datetime.combine( week_starts_of_sem[nb_week].date(), timeslot ) + timedelta( days=e['st'].weekday() )
                        
                        if e['st'] == datetime_slot:
                            nb_stripes_before = ( sum( [len(weekday_stripes[i]) for i in range(0,nb_wday)] ) + nb_stripe)
                            nb_spans_before = ( ((len(time_spans) + 1) * nb_week ) + nb_timeslot )
                            h = row_h if (e['type'] != ct_marker_LAB) else row_h*2 + row_space
                            x = left_space  +  nb_wday*col_skip  + (nb_stripes_before-1) * col_space + nb_stripes_before * col_w
                            y = top_space   +  nb_week*row_skip  + (nb_spans_before-1) * row_space + nb_spans_before * row_h

                            if color_by_course == 1 and e['course'] in course_colors.keys(): fill_color = course_colors[ e['course'] ]
                            elif color_by_room==1 and e['location'] in room_colors.keys(): fill_color = room_colors[ e['location'] ]
                            elif color_by_prof==1 and e['prof'] in prof_colors.keys(): fill_color = prof_colors[ e['prof'] ]
                            else: fill_color = 'white'

                            etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(col_w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill=fill_color )
                            y1 = y + h/2 + 3
                            
                            # Название предмета
                            tx = etree.Element( 'text', x=str(x + col_w/2), y=str(y1 - 3*float(h)/9), fill='black', style=txt_style_0b )
                            tx.text = e['course']; doc.append( tx ) # "N%03d" % e['id']
                            # Фамилия преподавателя
                            tx = etree.Element( 'text', x=str(x + col_w/2), y=str(y1 - 1*float(h)/9), fill='black', style=txt_style_0 )
                            tx.text = e['prof']; doc.append( tx )
                            # Тип занятия и кабинет
                            tx = etree.Element( 'text', x=str(x + col_w/2), y=str(y1 + 1*float(h)/9), fill='black', style=txt_style_0 )
                            s = e['type'];
                            if e['location'] != '': s = s + ' ' + e['location'];
                            tx.text = s; doc.append( tx )
                            # Название группы
                            tx = etree.Element( 'text', x=str(x + col_w/2), y=str(y1 + 3*float(h)/9), fill='black', style=txt_style_0 )
                            tx.text = e['group']; doc.append( tx )
    
    # ElementTree 1.2 doesn't write the SVG file header errata, so do that manually
    f = open( os.path.join(dst_dir_prefix, '%s' % f_name), 'w')
    f.write( '<?xml version=\"1.0\" standalone=\"no\"?>\n' )
    f.write( '<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\"\n' )
    f.write( '\"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n' )
    f.write( etree.tostring(doc, pretty_print = True) )
    f.close()














##############################
# Отрисовка листа с лекциями #
##############################

def draw_prof_presence_list( cal, fn='prof_list.svg', prof_list=prof_list ):
    
    T = [ [ list() for w in wdays[:-1] ] for p in prof_list ]
    for np,p in enumerate( prof_list ):
        for nw,w in enumerate( wdays[:-1] ):
            T[np][nw] = list( [ {'L':list(), 'ud':set()} for t in time_spans ] )

    # Наполнить таблицу
    rooms = set(); courses = set(); groups_list = set();
    n_stripes_per_prof = [ 0 for p in prof_list ]
    n_spans_in_week = [ 1 for w in wdays[:-1] ]
    n_spans_in_timeslot = [ [2 for t in time_spans] for w in wdays[:-1] ]
    nb_weeks_in_sem = 17

    for component in cal.walk():
        if component.name == "VEVENT" and component['prof'] in prof_list :# and component['first'] == 1: # and component['type'] in [ct_marker_PZ, ct_marker_LK] 
            rooms.add( component['location'] ); groups_list.add( component['group'] ); courses.add( component['course']);

            # component.get('date_time_start')
            st = datetime.strptime( component['date_time_start'], '%Y-%m-%d %H:%M:%S');
            #ft = component.get('date_time_end');
            ft = datetime.strptime( component['date_time_end'], '%Y-%m-%d %H:%M:%S');
            prof = component.get('prof');

            np = prof_list.index( prof ); nts = time_spans.index( st.time() ); nw = st.weekday();
            #print st, nts
            if len( [x for x in T[np][nw][nts]['L'] if x['updown'] == component['updown']] ) > 0:
                # не добавляем такой компонент
                continue;
            else:
                if (component['type'] != ct_marker_LAB) or (component['type'] == ct_marker_LAB and sum([1 for e in T[np][nw][nts]['L'] if e['type'] == ct_marker_LAB]) == 0):
                    T[np][nw][nts]['L'].append( component )
                    T[np][nw][nts]['ud'].add( component['updown'] ) # up, dn, updn
                    n_stripes_per_prof[np] = max( n_stripes_per_prof[np], len(T[np][nw][nts]['L']))
            #if len(T[np][nw][nts]['ud']) == 1 and 'updn' in T[np][nw][nts]['ud'] and n_spans_in_timeslot[nw][nts] < 2:
            #    n_spans_in_timeslot[nw][nts] = 1;
            #else: n_spans_in_timeslot[nw][nts] = 2


    # Раскраска -------------------------------------

    room_colors = {'':'white'}
    course_colors = {'':'white'}
    groups_colors = {'':'white'}
    profs_colors = {'':'white'}

    #cmap = cm.get_cmap('Pastel1') # Spectral, hsv, Paired, gist_rainbow
    cmap = cm.get_cmap('tab20')

    if len(rooms) > 0:
        for i,room in enumerate(sorted(rooms)): room_colors[room] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i) / (len(rooms)) )[0:3] ]) + ')'
    if len(courses) > 0:
        for i,course in enumerate(sorted(courses)): course_colors[course] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i) / (len(courses)) )[0:3] ]) + ')'
    if len( groups_list ) > 0:
        for i,groups in enumerate( sorted(groups_list) ): groups_colors[groups] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i) / (len(groups_list)) )[0:3] ]) + ')'
    if len( prof_list ) > 0:
        for i,profs in enumerate( sorted(prof_list) ): profs_colors[profs] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i+1) / (len(prof_list)+1) )[0:3] ]) + ')'

    # -----------------------------------------------

    n_spans_in_week = [ sum( n_spans_in_timeslot[nw] ) for nw,_ in enumerate(wdays[:-1]) ]
    
    nb_columns = len( prof_list )
    nb_rows = sum( n_spans_in_week ) # len( wdays ) * (len( time_spans ))

    col_w = 170; row_h = 40; rxy = 0; col_space = 0; row_space = 0; col_skip = 0; row_skip = 10; top_space = 80; left_space = 150;
    doc_w = left_space  +  nb_columns * (col_w + col_space)  +  (nb_columns - 1) * col_skip
    event_type_box_width = 40;
    wday_hat = 10;
    doc_h = top_space  + (len(wdays)-2)*row_skip  +  (len(wdays)-1)*(len(time_spans)+1)*row_space  +  nb_rows*row_h  +  5

    txt_style_0  = 'font-family:Sans;font-size:6px;text-anchor:middle;dominant-baseline:top' # Надписи на блоках
    txt_style_0b = txt_style_0 + ';font-weight:bold'
    txt_style_names = 'font-family:Sans;font-size:28px;text-anchor:middle;dominant-baseline:middle;text-anchor:middle' # Фамилии
    txt_style_1  = 'font-family:Sans;font-size:20px;text-anchor:middle;dominant-baseline:middle;text-anchor:middle' # Фамилии
    txt_style_2  = 'font-family:Sans;font-size:18px;text-anchor:middle;dominant-baseline:top' # Блоки описания недели
    txt_style_2sm= 'font-family:Sans;font-size:7px;text-anchor:middle;dominant-baseline:top' # Блоки описания недели
    txt_style_2b =  txt_style_2 + ';font-weight:bold'
    txt_style_4  = 'font-family:Sans;font-size:26px;text-anchor:middle;dominant-baseline:middle;text-anchor:middle'
    txt_style_4b = txt_style_4 + ';font-weight:bold'
    txt_style_5  = 'font-family:Sans;font-size:22px;text-anchor:middle;dominant-baseline:middle;text-anchor:middle'
    txt_style_5b = txt_style_5 + ';font-weight:bold'    
    txt_style_3  = 'font-family:Sans;font-size:48px;text-anchor:middle;dominant-baseline:top' # Дни недели

    # Соотношение сторон А4-----------------------------
    expected_w = doc_h * 210 / (297 - 10); # 30 мм на заголовок
    #expected_w = doc_h * 297 / (210 - 10); # 30 мм на заголовок
    
    col_w = (expected_w - left_space - nb_columns*col_space - (nb_columns - 1) * col_skip) / nb_columns
    doc_w = left_space  +  nb_columns * (col_w + col_space)  +  (nb_columns - 1) * col_skip + 2
    # --------------------------------------------------

    
    import lxml.etree as etree
    doc = etree.Element('svg', width=str(doc_w), height=str(doc_h), version='1.1', xmlns='http://www.w3.org/2000/svg')
    etree.SubElement( doc, 'rect', x=str(0), y=str(0), width=str(doc_w), height=str(doc_h), fill="white") # Белый фон
    
    # Фамилии преподавателей
    for nb_prof,prof in enumerate( prof_list ):
        nb_stripes_before = nb_prof
        nb_stripes_now    = 1
        w = nb_stripes_now * col_w  +  (nb_stripes_now-1) * col_space
        h = top_space - row_space
        x = left_space  +  nb_stripes_before * (col_w + col_space)  +  nb_prof * col_skip
        y = 0
        p_strings = len( prof_shorter[nb_prof].split('\n') )
        fill_stripe = "fill:#000000;fill-opacity:0.0;stroke:#000000;stroke-width:1"
        fill_header = "fill:%s;stroke:#000000;stroke-width:1" % profs_colors[prof]
        #if ( nb_prof % 2 ): fill_stripe = "fill:#000000;fill-opacity:0.0;stroke:#000000;stroke-width:1"
        #else: fill_stripe = "fill:#000000;fill-opacity:0.08;stroke:#000000;stroke-width:1"
        # fill="rgba(254,254,254,0.8)",
        etree.SubElement( doc, 'rect', x=str(x), y=str(0), width=str(w), height=str(doc_h), rx=str(rxy), ry=str(rxy), style=fill_stripe )
        etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(w), height=str(h), rx=str(rxy), ry=str(rxy), style=fill_header)
        tx = etree.Element( 'text', x=str(x + w/2), y=str(y + h/2 - 22 - 12*(p_strings-1)), height = str(h), fill='black', style=txt_style_names );
        doc.append( tx )
        i_prof = all_prof_list.index( prof )
        for t in prof_shorter[i_prof].split('\n'):
            txx = etree.Element( 'tspan', x=str(x + w/2), dy = '1.1em' );
            txx.text = t
            tx.append( txx )
    
    # Названия дней недели
    for nw,wk in enumerate( wdays[:-1] ):
        nb_spans_before = sum( n_spans_in_week[:nw] )
        nb_spans_now    = n_spans_in_week[nw]

        # Заголовок для недели
        h = wday_hat
        w = doc_w
        x = 0
        y = top_space  +  nw*row_skip  +  nb_spans_before * row_h   +   nw * (len(time_spans)+1) * row_space
        etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(doc_w), height=str(h), rx=str(rxy), stroke="black", style="fill:%s;fill-opacity:1" % wday_color[nw])        

        h = nb_spans_now * row_h   +  (len(time_spans)-1) * row_space  + 2 * row_space; #  +  nb_double_spans * row_space ################# 
        w = 2*float(left_space)/5  -  col_skip/4
        x = 0
        y = y + wday_hat
        etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(doc_w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill="rgba(254,254,254,0.8)", style="fill:#000000;fill-opacity:0" )
        etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(w),     height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill='white')
        #tx = etree.Element( 'text', x=str(x + w/2), y=str(y + h/2 + 24),  fill='black', style=txt_style_3 ); tx.text = wk; doc.append( tx )
        tx = etree.Element( 'text', x=str(x + w/2 + 16), y=str(y + h/2), fill='black', transform='rotate(-90,%s,%s)'%(x + w/2 + 16,y + h/2), style=txt_style_3 ); tx.text = wk; doc.append( tx )
        
        # Временные отрезки
        y1 = y + row_space
        for nb_timeslot,timeslot in enumerate( time_spans ):
            #nb_slots_before = sum( [ n_spans_in_week[nwl]['n'] for nwl,wl in enumerate(n_spans_in_week) if nwl < nw ] )
            nb_slots_now    = n_spans_in_timeslot[nw][nb_timeslot]
            w = 2*float(left_space)/5 - col_skip
            x = 2*float(left_space)/5 + col_skip/2
            h = nb_slots_now * row_h # + (nb_slots_now - 1) * row_space
            # Полоска
            etree.SubElement( doc, 'rect', x=str(x), y=str(y1), width=str(doc_w - x - col_space), height=str(nb_slots_now*row_h), \
                rx=str(rxy), ry=str(rxy), fill='white', style='fill:#ffffff;fill-opacity:0.0;;stroke:#000000;stroke-width:1' )
#               style='stroke:#606060;stroke-width:1;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1;stroke-miterlimit:4;stroke-dasharray:4,4;stroke-dashoffset:0;fill:#ffffff;fill-opacity:0.5'

            # Время начала
            etree.SubElement( doc, 'rect', x=str(x), y=str(y1), width=str(w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill='white')
            tx = etree.Element( 'text', x=str(x + w/2), y=str(y1 + h/2 - 4), fill='black', style=txt_style_2 );  tx.text = u'%d:%02d' %(timeslot.hour, timeslot.minute); doc.append( tx )
            # Время окончания
            dummydate = datetime(1, 1, 1, timeslot.hour, timeslot.minute, timeslot.second)
            timeslot_end = dummydate + timedelta( hours=1, minutes=30 );
            tx = etree.Element( 'text', x=str(x + w/2), y=str(y1 + h/2 + 20), fill='black', style=txt_style_2 );  tx.text = u'%d:%02d' %(timeslot_end.hour, timeslot_end.minute); doc.append( tx )

            # Верхняя и нижняя недели
            w = float(left_space)/5 - col_skip
            x = 4*float(left_space)/5 + col_skip/2
            h = row_h
            etree.SubElement( doc, 'rect', x=str(x), y=str(y1), width=str(w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill='white')
            tx = etree.Element( 'text', x=str(x + w/2), y=str(y1 + h/2 + 8), fill='black', style=txt_style_2 );  tx.text = u'в.н'; doc.append( tx )
            y2 = y1 + row_h;
            etree.SubElement( doc, 'rect', x=str(x), y=str(y2), width=str(w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill='#aaaaaa')
            tx = etree.Element( 'text', x=str(x + w/2), y=str(y2 + h/2 + 8), fill='white', style=txt_style_2 );  tx.text = u'н.н'; doc.append( tx )

            y1 += nb_slots_now * row_h  +  row_space  # (nb_slots_now - 1) * row_space  +  row_space

    
    # Занятия
    for np,Tpr in enumerate(T):
        nb_stripes_before = np
        nb_stripes_now    = 1
        
        x0 = left_space  +  nb_stripes_before * (col_w + col_space)  +  np * col_skip

        # Лабораторные
        for nw,Twd in enumerate( Tpr ):
            nb_spans_before = sum( n_spans_in_week[:nw] )
            nb_spans_now    = n_spans_in_week[nw]
            #y0 = top_space  +  nw*row_skip  +  wday_hat  +  nb_spans_before * row_h   +   nw * (nts+1) * row_space  + row_space  +  nw * row_space
            y0 = top_space  +  nw*row_skip  +  wday_hat  +  nb_spans_before * row_h   +   nw * row_space
            
            for nts,Tt in enumerate( Twd ):
                if len( Tt['L'] ) > 0:
                    nb_slots_before = sum( n_spans_in_timeslot[nw][:nts] )
                    nb_slots_now    = n_spans_in_timeslot[nw][nts]
                    x1 = x0
                    y1 = y0  +  nb_slots_before * row_h  +  nts * row_space
                    for i,evt in enumerate( Tt['L'] ):
                        if evt['type'] != ct_marker_LAB: continue;
                        y2 = y1
                        h = 4 * row_h + row_space
                        w = event_type_box_width
                        etree.SubElement( doc, 'rect', x=str(x1), y=str(y2), width=str(w), height=str(h), style='fill:#aaaaaa;fill-opacity:1;stroke:#000000;stroke-width:1' )
                        tx = etree.Element( 'text', x=str(x1 + w/2), y=str(y2 + h/2 + 10), fill='#ffffff', style=txt_style_5b );  tx.text = evt['type']; doc.append( tx )
                        #tx = etree.Element( 'text', x=str(x1 + w/2), y=str(y2 + h/2 + 10-40), fill='#ffffff', style=txt_style_5b );  tx.text = u"Л"; doc.append( tx )
                        #tx = etree.Element( 'text', x=str(x1 + w/2), y=str(y2 + h/2 + 10), fill='#ffffff', style=txt_style_5b );  tx.text = u"A"; doc.append( tx )
                        #tx = etree.Element( 'text', x=str(x1 + w/2), y=str(y2 + h/2 + 10+40), fill='#ffffff', style=txt_style_5b );  tx.text = u"Б"; doc.append( tx )
                        # Коробка события
                        x2 = x1 + event_type_box_width
                        w = col_w - event_type_box_width
                        etree.SubElement( doc, 'rect', x=str(x2), y=str(y2), width=str(w), height=str(h), style='fill:#cccccc;fill-opacity:0.2;stroke:#000000;stroke-width:1' )

                        #########################################################
                        #                                                       #
                        # Под описаниями лабораторных находится гребёнка недель #
                        #                                                       #
                        #########################################################

                        square_h = 10
                        week_nbs = [int(x) for x in evt['WEEK_NUMBERS'].split(',')]
                        for wk in range(1,nb_weeks_in_sem+1):
                            xx = x1+event_type_box_width+(wk-1)*w/nb_weeks_in_sem
                            yy = y2+h-square_h
                            ww = w/(nb_weeks_in_sem)
                            if wk in week_nbs:
                                etree.SubElement( doc, 'rect', \
                                    x=str(xx), width=str(ww), y=str(yy), height=str(square_h), \
                            	    style='fill:#000000;fill-opacity:1;stroke:#000000;stroke-width:1' )
                                tx = etree.Element( 'text', x=str(xx + square_h/2), y=str(yy + 8), \
                                    fill='#ffffff', style=txt_style_2sm );  tx.text = str(wk); doc.append( tx )
                            else:
                                etree.SubElement( doc, 'rect', \
                                    x=str(xx), width=str(ww), y=str(yy), height=str(square_h), \
                            	    style='fill:#ffffff;fill-opacity:0;stroke:#000000;stroke-width:1' )




        # Лекции или практика
        for nw,Twd in enumerate( Tpr ):
            #nb_spans_before = sum( [ n_spans_in_week[nwl] for nwl,_ in enumerate(n_spans_in_week) if nwl < nw ] )
            nb_spans_before = sum( n_spans_in_week[:nw] )
            nb_spans_now    = n_spans_in_week[nw]
            #nb_double_spans = n_spans_in_week[nw] - len(time_spans)
            #y0 = top_space  +  nw * row_skip  +  nb_spans_before * (row_space + row_h)  +  row_space
            y0 = top_space  +  nw*row_skip  +  wday_hat  +  nb_spans_before * row_h   +   nw * (nts+1) * row_space  + row_space  +  nw * row_space
            for nts,Tt in enumerate( Twd ):
                if len( Tt['L'] ) > 0:
                    nb_slots_before = sum( n_spans_in_timeslot[nw][:nts] )
                    nb_slots_now    = n_spans_in_timeslot[nw][nts]
                    x1 = x0
                    y1 = y0  +  nb_slots_before * row_h  +  nts * row_space
                    fill_color = 'rgb(255, 255, 230)'
                    for i,evt in enumerate( Tt['L'] ):

                        if evt['type'] == ct_marker_LAB: continue;

                        y2 = y1
                        #print nb_slots_now, evt['updown']
                        h = nb_slots_now * row_h
                        # Изменения в стиле
                        #if evt['group'] in groups_colors.keys(): fill_color = groups_colors[ evt['group'] ]
                        #if evt['location'] in room_colors.keys(): fill_color = room_colors[ evt['location'] ]
                        if evt['prof'] in profs_colors.keys(): fill_color = profs_colors[ evt['prof'] ]
                        
                        if evt['updown'] == 'up': h = row_h;
                        if evt['updown'] == 'dn': h = row_h; y2 = y1 + row_h;
                        dx = dy = 0 # -5 * (len(Tt['L']) - i - 1)

                        # Лекция или практика
                        w = event_type_box_width
                        if evt['type'] == ct_marker_PZ:
                            etree.SubElement( doc, 'rect', x=str(x1), y=str(y2), width=str(w), height=str(h), style='fill:#cc0000;fill-opacity:1;stroke:#000000;stroke-width:1' )
                            tx = etree.Element( 'text', x=str(x1 + w/2 + dx), y=str(y2 + h/2 + 8), fill='white', style=txt_style_5b );  tx.text = evt['type']; doc.append( tx )
                        else:
                            etree.SubElement( doc, 'rect', x=str(x1), y=str(y2), width=str(w), height=str(h), style='fill:#00aa99;fill-opacity:1;stroke:#000000;stroke-width:1' )
                            tx = etree.Element( 'text', x=str(x1 + w/2 + dx), y=str(y2 + h/2 + 8), fill='white', style=txt_style_5b );  tx.text = evt['type']; doc.append( tx )
                        # Коробка события
                        x2 = x1 + event_type_box_width
                        w = col_w - event_type_box_width
                        etree.SubElement( doc, 'rect', x=str(x2 + dx), y=str(y2 + dy), width=str(w), height=str(h), style='fill:%s;fill-opacity:0.6;stroke:#000000;stroke-width:1' % fill_color )
                        #etree.SubElement( doc, 'rect', x=str(x2 + dx), y=str(y2 + dy), width=str(w), height=str(h), style='fill:#ffffd0;fill-opacity:1;stroke:#000000;stroke-width:1' )
                        #                              rx=str(rxy), ry=str(rxy), 
                        #tx = etree.Element( 'text', x=str(x2 + w/2 + dx), y=str(y2 + h/2 + dy + 6), fill='black', style=txt_style_2 );  tx.text = evt['group']; doc.append( tx )
                        # Надписи на событии
                        if evt['updown'] == 'updn':
                            tx = etree.Element( 'text', x=str(x2 + w/2 + dx), y=str(y2 + h/2 - 7), fill='black', style=txt_style_4 );  tx.text = short_group_name(evt['group']); doc.append( tx )
                            tx = etree.Element( 'text', x=str(x2 + w/2 + dx), y=str(y2 + h/2 + 26), fill='black', style=txt_style_4b );  tx.text = short_room_name(evt['location']); doc.append( tx )
                        else:
                            tx = etree.Element( 'text', x=str(x2 + w/2 - 30), y=str(y2 + h/2 + 7), fill='black', style=txt_style_2 );  tx.text = short_group_name(evt['group']); doc.append( tx )
                            tx = etree.Element( 'text', x=str(x2 + w/2 + 36), y=str(y2 + h/2 + 7), fill='black', style=txt_style_2b );  tx.text = short_room_name(evt['location']); doc.append( tx )

    f = open( os.path.join('%s' % fn), 'w')
    f.write( '<?xml version=\"1.0\" standalone=\"no\"?>\n' )
    f.write( '<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\"\n' )
    f.write( '\"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n' )
    f.write( etree.tostring(doc, pretty_print = True) )
    f.close()












# Добавить более длинные занятия
# Если больше одного занятия в клетке, уменьшить ширину окна для данного занятия (при той же длине)
#    перекрывающиеся занятия будут находиться рядом
def draw_prof_personal_sheet( cal, selected_prof='', selected_room='', selected_group = '', selected_course = '', \
                              color_by_course = 0, color_by_room=0, color_by_prof=0, color_by_group=0, f_name = 'sample',
                              draw_every_timeslot = 0 ):
    
    txt_style_0  = 'font-family:Sans;font-size:6px;text-anchor:middle;dominant-baseline:top'  # Надписи на блоках
    txt_style_0b = txt_style_0 + ';font-weight:bold'
    txt_style_1  = 'font-family:Sans;font-size:14px;text-anchor:middle;dominant-baseline:middle;text-anchor:middle' # Фамилии
    txt_style_2  = 'font-family:Sans;font-size:14px;text-anchor:middle;dominant-baseline:middle' # Блоки описания недели
    txt_style_22 = 'font-family:Sans;font-size:13px;text-anchor:middle;dominant-baseline:middle' # Блоки временных интервалов
    txt_style_2b =  txt_style_2 + ';font-weight:bold'
    txt_style_2bsm  = txt_style_2b.replace( 'font-size:14px;', 'font-size:12px;' )
    txt_style_2bsm2  = txt_style_2b.replace( 'font-size:14px;', 'font-size:12px;' )
    txt_style_2sm  = txt_style_2.replace( 'font-size:14px;', 'font-size:10px;' )
    txt_style_2smm = txt_style_2.replace( 'font-size:14px;', 'font-size:8px;' )
    txt_style_3  = 'font-family:Sans;font-size:32px;text-anchor:middle;dominant-baseline:top' # Дни недели
    
    nb_weeks = (sem_finish + timedelta(days = 7-sem_finish.weekday()) - (sem_start - timedelta(days = sem_start.weekday()) )).days / 7
    
    T = [ [ [ list() for nts,_ in enumerate( time_spans ) ] for w in wdays[:-1] ] for nw in range(0,nb_weeks) ]
    for nw in range(0,nb_weeks):
        for nwd,_ in enumerate( wdays[:-1] ):
            for nts,_ in enumerate( time_spans ):
                T[nw][nwd][nts] = list()
    
    # Заполнить таблицу
    n_timeslots_in_weekday = [[ 0 for nts in time_spans ] for wd in wdays[:-1]]
    n_timeslots_in_weekday_set = [ set() for wd in wdays[:-1]]

    # Если мы хотим чтобы в расписании находились все временные отрезки, а не только занятые парами
    if draw_every_timeslot > 0:
        for nwd,_ in enumerate( wdays[:-1] ):
            if draw_every_timeslot == 1: # Рисовать все временные окна
                for nts,timeslot in enumerate( time_spans ):
                    n_timeslots_in_weekday_set[nwd].add( timeslot );
            if draw_every_timeslot == 2: # Только дневные временные окна
                for nts,timeslot in enumerate( time_spans[:-2] ):
                    n_timeslots_in_weekday_set[nwd].add( timeslot );

    n_timeslots_in_weekday_len = [ dict() for wd in wdays[:-1]]
    
    # Заготовки для расцветки
    room_colors = {'':'white'}
    course_colors = {'':'white'}
    groups_colors = {'':'white'}
    rooms = set(); courses = set(); groups_list = set();

    #prof_calendar = Calendar()
    #prof_calendar.add('version', '3.0')
    #prof_calendar.add('prodid', '-//test file//example.com//')
    #prof_calendar.add('X-WR-CALNAME', u"%s - Расписание" % selected_prof )
    
    for component in cal.walk():
        if component.name == "VEVENT" and \
                ( selected_prof == '' or component['prof'] == selected_prof ) and \
                ( selected_room == '' or component['location'] == selected_room ) and \
                ( selected_group == '' or selected_group in component['groups'].split(' ') ):
                #component['type'] == ct_marker_LAB and \
            rooms.add( component['location'] ); groups_list.add( component['group'] ); courses.add( component['course']);

            #if component['first'] == 1:
            #    event = Event()
            #    event['dtstart'] = component['dtstart']; event['dtend']   = component['dtend']; event['location'] = component['location'];
            #    event['rrule']   = component['rrule'];   event['summary'] = component['summary'] # + "(%s)" % component['groups']
            #    prof_calendar.add_component( event )
            
            #st = component.get('date_time_start');
            st = datetime.strptime( component['date_time_start'], '%Y-%m-%d %H:%M:%S');
            #et = component.get('date_time_start');
            #ft = datetime.strptime( component['date_time_end'], '%Y-%m-%d %H:%M:%S');
            ud = component.get('updown'); nwd = st.weekday();

            rrset = rrule.rruleset()
            rrset.rrule( rrule.rrulestr( component.get('rrule').to_ical(), dtstart = st ) )
            #rr = rrule.rrule(freq=rrule.HOURLY, dtstart=dtstart, until=dtuntil)
            for evt in list(rrset):
              if evt > sem_finish: continue;
              nw = (( evt + timedelta(days = 7-evt.weekday()) - (sem_start - timedelta(days = sem_start.weekday()) ))).days / 7 - 1      # ?-1
              timeslot = evt.time(); nts = time_spans.index( timeslot );
              T[nw][nwd][nts].append( component )
              # Сколько в каждом дне недели будет временных отрезков (вспомогательная часть)
              #if draw_every_timeslot == 0:
              n_timeslots_in_weekday_set[nwd].add( timeslot )
              # event_length = (et - st).minutes
              event_length = 2 if component['type'] == ct_marker_LAB else 1;
              n_timeslots_in_weekday_len[nwd][timeslot] = event_length
              if component['type'] == ct_marker_LAB: n_timeslots_in_weekday_set[nwd].add( time_spans[nts+1] )


    cmap = cm.get_cmap('Pastel1') # Spectral, hsv, Paired, gist_rainbow
    if len(rooms) > 0:
        for i,room in enumerate(sorted(rooms)): room_colors[room] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i) / (len(rooms)) )[0:3] ]) + ')'
    if len(courses) > 0:
        for i,course in enumerate(sorted(courses)): course_colors[course] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i) / (len(courses)) )[0:3] ]) + ')'
    if len( groups_list ) > 0:
        for i,groups in enumerate( sorted(groups_list) ): groups_colors[groups] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i) / (len(groups_list)) )[0:3] ]) + ')'
    
    # Сколько временных отрезков должно быть нарисовано в каждый день недели
    n_timeslots_in_weekday_sum = [ sum( 1 for n in n_timeslots_in_weekday_set[nwd] ) for nwd,_ in enumerate( wdays[:-1] ) ]
    n_timeslots_in_weekday_min = [ max( 1,n ) for n in n_timeslots_in_weekday_sum ]
    
    nb_columns = nb_weeks
    nb_rows = sum(n_timeslots_in_weekday_min)
    nb_timespans = sum(n_timeslots_in_weekday_min)
    
    col_w = 50; row_h = 40; rxy = 5; col_space = 4; row_space = 5; col_skip = 5; row_skip = 20; top_space = 40; left_space = 110; date_space = 16;
    doc_w = left_space  +  nb_columns * col_w  +  (nb_columns - 1)*col_space

    expected_h = doc_w * 210 / 297; # Соотношение сторон как у листа A4
    row_h = (expected_h - top_space - (len(wdays)-2) * row_skip  -  (nb_timespans + (len(wdays)-1)) * row_space  - (len(wdays) - 1)*(date_space + row_space)) / nb_rows
    if row_h < 30: # row_h = 30;
        expected_h = doc_w * 297 / 210; # Портретная ориентация
        row_h = (expected_h - top_space - (len(wdays)-2) * row_skip  -  (nb_timespans + (len(wdays)-1)) * row_space  - (len(wdays) - 1)*(date_space + row_space)) / nb_rows        
    doc_h = top_space  + (len(wdays)-2) * row_skip  +  (nb_timespans + (len(wdays)-1)) * row_space  +  nb_rows * row_h  +  (len(wdays) - 1)*(date_space + row_space)
    
    import lxml.etree as etree
    doc = etree.Element('svg', width=str(doc_w), height=str(doc_h), version='1.1', xmlns='http://www.w3.org/2000/svg')
    etree.SubElement( doc, 'rect', x=str(0), y=str(0), width=str(doc_w), height=str(doc_h), fill="white") # Белый фон

    tx = etree.Element( 'text', x=str(left_space/2), y=str(top_space/2 + 8), height = str(top_space), width=str(left_space), fill='black', style=txt_style_1 );
    tx.text = u''
    if selected_prof != '': tx.text += selected_prof
    if selected_room != '': tx.text += selected_room
    if selected_group != '': tx.text += selected_group
    if selected_course != '': tx.text += selected_course
    doc.append( tx )
    
    # Номера недель
    for nw in range(0,nb_weeks):
        w = col_w
        h = top_space - row_skip
        x = left_space  +  nw * (col_w + col_space)
        y = 0
        #fill_stripe = "fill:#000000;fill-opacity:0.05" if ( nw % 2 ) else "fill:#000000;fill-opacity:0.15"
        fill_stripe = "fill:#000000;fill-opacity:0.00" if ( nw % 2 ) else "fill:#000000;fill-opacity:0.05"
        etree.SubElement( doc, 'rect', x=str(x), y=str(0), width=str(w), height=str(doc_h), rx=str(rxy), ry=str(rxy), fill="rgba(254,254,254,0.8)", style=fill_stripe )
        etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill='white')
        tx = etree.Element( 'text', x=str(x + w/2), y=str(y + h/2 + 8), height = str(h), fill='black', style=txt_style_1 ); tx.text = str(nw+1); doc.append( tx )

    # Названия дней недели
    for nwd,wkd in enumerate( wdays[:-1] ):
        nb_spans_before = sum( n_timeslots_in_weekday_min[:nwd] )
        nb_timeslots_before = sum( n_timeslots_in_weekday_min[:nwd] )
        #len_spans_before = sum( n_timeslots_in_weekday_len_sum[:nwd] )
        nb_spans_now     = n_timeslots_in_weekday_min[nwd]
        nb_timeslots_now = n_timeslots_in_weekday_min[nwd]
        h = nb_spans_now * row_h   +  (nb_timeslots_now + 1) * row_space  +  row_space  + date_space
        w = 3*float(left_space)/5  -  col_skip/4
        x = 0
        y = top_space  +  nwd*(row_skip + row_space + date_space)  +  nb_spans_before * row_h   +   (nb_timeslots_before + nwd) * row_space
        etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(doc_w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill="rgba(254,254,254,0.8)", style="fill:#000000;fill-opacity:0.05" )
        etree.SubElement( doc, 'rect', x=str(x), y=str(y), width=str(w),     height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill='white')
        tx = etree.Element( 'text', x=str(x + w/2), y=str(y + h/2 + 18),  fill='black', style=txt_style_3 ); tx.text = wkd; doc.append( tx )

        # Скруглённые прямоугольники с текущей датой
        for nw in range(0,nb_weeks):
            dt = (sem_start + timedelta(days = -sem_start.weekday() + nw*7 + nwd)  ).date()
            ds = dt.strftime("%d.%m")
            yd = y + row_space
            xd = left_space  +  nw * (col_w + col_space)
            # С запасом по ширине +- 1 единица
            etree.SubElement( doc, 'rect', x=str(xd+1), y=str(yd), width=str(col_w-2), height=str(date_space), rx=str(date_space/2), ry=str(date_space/2), stroke="lightgrey", fill='white')
            tx = etree.Element( 'text', x=str(xd + col_w/2), y=str(yd + date_space/2 + 5), fill='black', style=txt_style_2 );  tx.text = ds; doc.append( tx )

        # Временные отрезки
        y1 = y + row_space + date_space + row_space
        for nb_timeslot,timeslot in enumerate( sorted( n_timeslots_in_weekday_set[nwd] ) ):
            nts = time_spans.index( timeslot );
            w = 2*float(left_space)/5 - col_skip
            x = 3*float(left_space)/5 + col_skip/2
            h = row_h
            # Полоска
            etree.SubElement( doc, 'rect', x=str(x), y=str(y1), width=str(doc_w - x), height=str(h), rx=str(rxy), ry=str(rxy), fill='white', style='fill:#ffffff;fill-opacity:0.5' )
            etree.SubElement( doc, 'rect', x=str(x), y=str(y1), width=str(w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill='white')
            #tx = etree.Element( 'text', x=str(x + w/2), y=str(y1 + h/2 + 8), fill='black', style=txt_style_2 );  tx.text = u'%d:%02d' %(timeslot.hour, timeslot.minute); doc.append( tx )

            # Время начала
            etree.SubElement( doc, 'rect', x=str(x), y=str(y1), width=str(w), height=str(h), rx=str(rxy), ry=str(rxy), stroke="black", fill='white')
            tx = etree.Element( 'text', x=str(x + w/2), y=str(y1 + h/2 - 3), fill='black', style=txt_style_22 );  tx.text = u'%d:%02d' %(timeslot.hour, timeslot.minute); doc.append( tx )
            # Время окончания
            dummydate = datetime(1, 1, 1, timeslot.hour, timeslot.minute, timeslot.second)
            timeslot_end = dummydate + timedelta( hours=1, minutes=30 );
            tx = etree.Element( 'text', x=str(x + w/2), y=str(y1 + h/2 + 12), fill='black', style=txt_style_22 );  tx.text = u'%d:%02d' %(timeslot_end.hour, timeslot_end.minute); doc.append( tx )
            
            y1 += h  +  row_space  # (nb_slots_now - 1) * row_space  +  row_space

        y1 = y + row_space + date_space + row_space
        # События на этом отрезке (должны быть поверх всех отрезков)
        for nb_timeslot,timeslot in enumerate( sorted( n_timeslots_in_weekday_set[nwd] ) ):
            nts = time_spans.index( timeslot );
            for nw in range(0,nb_weeks):
                #this_slot_events = T[nw][nwd][nts]
                d_ev_nb = 0
                x_skip = 0
                # Если в этом слоте есть лабораторные, добавить к количеству событий события следующего слота
                if nts < (len(time_spans)-1) and len( [ev for ev in T[nw][nwd][nts] if ev['type'] == ct_marker_LAB ] ):
                    d_ev_nb = len( T[nw][nwd][nts+1] )
                # Если в предыдущем слоте были лабораторные, добавить к количеству событий
                # количество в предыдущем слоте, и сместить всё на x_skip
                if nts > 0 and len( [ev for ev in T[nw][nwd][nts-1] if ev['type'] == ct_marker_LAB ] ):
                    x_skip = d_ev_nb = len( T[nw][nwd][nts-1] )

                if len( T[nw][nwd][nts] ) > 0:
                    w = col_w / (len( T[nw][nwd][nts] ) + d_ev_nb)
                    x = left_space  +  nw * (col_w + col_space)
                    # Первый раз -- для прямоугольников
                    for nev,evt in enumerate( T[nw][nwd][nts] ):
                    	st = datetime.strptime( evt['date_time_start'], '%Y-%m-%d %H:%M:%S');
                        if st.strftime('%d.%m') in holidays: continue;

                        x1 = x + (nev + x_skip) * w
                        h_ev = 2*row_h + row_space if evt['type'] == ct_marker_LAB else row_h # n_timeslots_in_weekday_len[nwd][timeslot]

                        if color_by_course == 1 and evt['course'] in course_colors.keys(): fill_color = course_colors[ evt['course'] ]
                        elif color_by_group == 1 and evt['group'] in groups_colors.keys(): fill_color = groups_colors[ evt['group'] ]
                        elif color_by_room==1 and evt['location'] in room_colors.keys(): fill_color = room_colors[ evt['location'] ]
                        elif color_by_prof==1 and evt['prof'] in prof_colors.keys(): fill_color = prof_colors[ evt['prof'] ]
                        else: fill_color = 'white'

                        etree.SubElement( doc, 'rect', x=str(x1), y=str(y1), width=str(w), height=str(h_ev), rx=str(rxy), ry=str(rxy), stroke="black", fill=fill_color )
                    # Второй раз -- чтобы текст был поверх прямоугольников
                    for nev,evt in enumerate( T[nw][nwd][nts] ):
                    	st = datetime.strptime( component['date_time_start'], '%Y-%m-%d %H:%M:%S');
                        if st.strftime('%d.%m') in holidays: continue;

                        labels = []; shift = []; style = [];
                        if selected_course == '': labels.append( evt['course']   );  shift.append(-1.5); # 0

                        style.append( txt_style_2sm )
                        #if len( evt['course'] ) >= 6: style.append( txt_style_2bsm2 );
                        #elif len( evt['course'] ) == 5: style.append( txt_style_2bsm );
                        #else: style.append( txt_style_2b );

                        if selected_group == '':  labels.append( short_group_name(evt['group'])    ); style.append( txt_style_2bsm2 ); shift.append(-1); # 0
                        if selected_room == '':   labels.append( short_room_name(evt['location']) ); style.append( txt_style_2sm );  shift.append(-1);
                        if selected_prof == '':   labels.append( evt['prof']     ); style.append( txt_style_2smm ); shift.append(0);
                        n_str = float(len( labels ))
                        
                        x1 = x + (nev + x_skip) * w
                        h_ev = 2*row_h if evt['type'] == ct_marker_LAB else row_h
                        for i,dy in enumerate( np.linspace( -h_ev/3.5, h_ev/3.5, n_str ) ):
                            tx = etree.Element( 'text', x = str( x1 + w/2 ), \
                                y = str( y1 + 6 + h_ev/2 + shift[i] + dy ), \
                                fill = 'black', textLength=str(col_w), \
                                style = style[i] );
                            tx.text = labels[i]; doc.append( tx )
            y1 += h  +  row_space  # (nb_slots_now - 1) * row_space  +  row_space    
    

    f = open(os.path.join(dst_dir_prefix, '%s' % f_name), 'w')
    f.write( '<?xml version=\"1.0\" standalone=\"no\"?>\n' )
    f.write( '<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\"\n' )
    f.write( '\"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n' )
    f.write( etree.tostring(doc, pretty_print = True) )
    f.close()

    #if "prof" in f_name and "by_group" in f_name and not "all_timeslots" in f_name:
    #    f = open( 'out/%s.cal' % f_name, 'wb')
    #    s = prof_calendar.to_ical().replace('\\;',';' ).replace('\\,',',' )
    #    f.write( s )
    #    f.close()

        #qr = qrcode.QRCode( version=1,
        #                    error_correction=qrcode.constants.ERROR_CORRECT_L,
        #                    box_size=15,
        #                    border=4,
        #                  )
        #qr.add_data( s )
        #qr.make(fit=True)

        #img = qr.make_image( fill_color="black", back_color="white" )
        #img.save( u"%s.png" % selected_prof )



###########################
# Открыть общий календарь #
###########################

if len( sys.argv ) > 1: src_dir_prefix = sys.argv[1]
else: src_dir_prefix = ''

if len( sys.argv ) > 2: dst_dir_prefix = sys.argv[2]
else: dst_dir_prefix = ''

gfile = open( os.path.join(src_dir_prefix, 'cal/all.cal') ,'rb' )
gcal = Calendar.from_ical(gfile.read())
#for component in gcal.walk():
#    print component.name


rooms = set( e['location'] for e in gcal.walk() if e.name == "VEVENT" and len(e['location']) != 0 )
courses = set( e['course'] for e in gcal.walk() if e.name == "VEVENT" and e['course'] != '' )
cmap = cm.get_cmap('Set3') # Spectral, hsv, Paired, gist_rainbow


if len(rooms) > 1:
    for i,room in enumerate(sorted(rooms)): room_colors[room] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i) / (len(rooms)-1) )[0:3] ]) + ')'
if len(courses) > 1:
    for i,course in enumerate(sorted(courses)): course_colors[course] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i) / (len(courses)-1) )[0:3] ]) + ')'
groups_lists = set( e['group'] for e in gcal.walk() if e.name == "VEVENT" )
if len(groups_lists) > 1:
    for i,groups in enumerate( sorted(groups_lists) ): groups_colors[groups] = 'rgb(' + ', '.join( [str(int(255*x)) for x in cmap( float(i) / (len(groups_lists)-1) )[0:3] ]) + ')'



#all_groups = [gl.split(' ') for gl in groups_lists]
#for gl in all_groups: print gl
groups = set(  );
for gl in groups_lists:
    for g in gl.split(' '): groups.add( g )

#for r in rooms: draw_prof_room( selected_room = r, f_name = 'room_'+r );
#for p in prof_list: draw_prof_room( selected_prof = p, f_name = 'prof_'+p+'_by_room' );
#for p in prof_list: draw_prof_room( selected_prof = p, color_by_course = 1, f_name = 'prof_'+p+'_by_course' );
#for g in groups: draw_prof_room( selected_group = g, color_by_course = 1, f_name = 'group_'+g );

# График присутствия по лекциям
if len( sys.argv ) > 3 and 'total' in sys.argv[3:]:
	prof_list = prof_list_303
	draw_prof_presence_list( cal=gcal, fn='total_lec_list_303.svg', prof_list=prof_list_303 )
	
	prof_list = prof_list_305
	draw_prof_presence_list( cal=gcal, fn='total_lec_list_305.svg', prof_list=prof_list_305 )
	
	prof_list = all_prof_list
	draw_prof_presence_list( cal=gcal, fn='total_lec_list.svg' )

	draw_prof_room( cal=gcal, color_by_prof = 1, f_name = 'total_by_prof' )
	draw_prof_room( cal=gcal, color_by_room = 1, f_name = 'total_by_room' )


#draw_prof_labs_2( cal=gcal, f_name='total_labs.svg' ) # ct_marker_LAB, 
#draw_prof_labs_2( cal=gcal, f_name='total_lec_pract.svg', what2draw=[ct_marker_LK, ct_marker_PZ])

#draw_prof_labs( f_name='total_labs.svg' )
#draw_prof_labs_3( f_name='total_labs_3.svg', prof_list=prof_list )

#print sys.argv
#print len( sys.argv )
#print '=========================='
#
#arg_list = []


#if len( sys.argv ) == 1: arg_list = ['all']
#if len( sys.argv ) > 3:
#	for a in sys.argv[3:]:
#		#print a
#		if a == 'rooms' : arg_list = arg_list + list(rooms)
#		elif a == 'groups': arg_list = arg_list + list(groups)
#		elif a == 'profs' : arg_list = arg_list + list(profs)
#		else: arg_list.append( a.decode('utf-8') )

#if len(arg_list) > 0: draw_result( cal=gcal, selection=arg_list, f_name = 'schedule' )
#print arg_list




#for a in arg_list:
#  #draw_result( cal=gcal, selection=a, f_name = 'schedule'+'_'+a )

#for a in arg_list:
#    tag = tag_me( a )[0]
#    print a, tag
#    #if tag == 'room': draw_result( cal=gcal, selected_room = a, f_name = 'schedule_'+tag+"_"+a )
#    #if tag == 'prof': draw_result( cal=gcal, selected_prof = a, f_name = 'schedule_'+tag+"_"+a )
#    #if tag == 'group_list' or tag == 'group': draw_result( cal=gcal, selected_group = a, f_name = 'schedule_'+tag+"_"+a )
#    #if a == 'all' : draw_prof_presence_list( cal=gcal, fn='total_lec_list.svg' )




# Нарисовать все расписания по группам, комнатам и преподавателям

#### restore this
if len( sys.argv ) > 3 and 'profs' in sys.argv[3:]:
  for p in prof_list: draw_prof_personal_sheet( cal=gcal, selected_prof = p, f_name = 'prof_'+p+'_by_group', color_by_group = 1 );
  #for p in prof_list: draw_prof_personal_sheet( cal=gcal, selected_prof = p, f_name = 'prof_'+p+'_by_group_all_timeslots', color_by_group = 1, draw_every_timeslot=1 );
#for p in prof_list: draw_prof_personal_sheet( cal=gcal, selected_prof = p, f_name = 'prof_'+p+'_by_room', color_by_room = 1 );
#for p in prof_list: draw_prof_personal_sheet( cal=gcal, selected_prof = p, f_name = 'prof_'+p+'_by_group_all_day_timeslots', color_by_group = 1 )#, #draw_every_timeslot=2 );


#### restore this
if len( sys.argv ) > 3 and 'rooms' in sys.argv[3:]:
  for r in rooms: draw_prof_personal_sheet( cal=gcal, selected_room = r, f_name = 'room_'+r+'_by_prof', color_by_prof = 1 );
  #for r in rooms: draw_prof_personal_sheet( cal=gcal, selected_room = r, f_name = 'room_'+r+'_by_group', color_by_group = 1 );
  #for r in rooms: draw_prof_personal_sheet( cal=gcal, selected_room = r, f_name = 'room_'+r );
#### restore this

if len( sys.argv ) > 3 and 'groups' in sys.argv[3:]:
    for g in groups: draw_prof_personal_sheet( cal=gcal, selected_group = g, color_by_course = 1, f_name = 'group_'+g );

# Нарисовать три образца расписания для отладки
#p = prof_list[0];     draw_prof_personal_sheet( selected_prof = p, f_name = 'prof_'+p+'_by_room', color_by_room = 1 );
#r = list(rooms)[10];  draw_prof_personal_sheet( selected_room = r, f_name = 'room_'+r+'_by_prof', color_by_prof = 1 );
#g = list(groups)[10]; draw_prof_personal_sheet( selected_group = g, color_by_course = 1, f_name = 'group_'+g );

#draw_prof_personal_sheet( selected_prof = prof_list[0], color_by_course = 1 );

# Вывести календарь
#f = open( 'example.ics', 'wb' )
#f.write(cal.to_ical())
#f.close()

gfile.close()
