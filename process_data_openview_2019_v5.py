# -*- coding: utf-8 -*-
import numpy as np
import h5py
import string
import matplotlib.pyplot as plt 
import seaborn as sns
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import requests
from bs4 import BeautifulSoup
import pickle

def make_set(author_sum_t2):
	author_set=set()
	for ll in author_sum_t2:
		if type(ll)==str:
			author_set.add(ll)
		else:
			for l2 in ll:
				author_set.add(l2)
	return author_set

def find_delete(author_sum_t2):
	delete_mark=[]
	for kk in range(len(author_sum_t2)):
		if type(author_sum_t2[kk])==str:
			if author_sum_t2[kk]=='[Deleted]':
				delete_mark.append(kk)
		else:
			for jj in range(len(author_sum_t2[kk])):
				if author_sum_t2[kk][jj]=='[Deleted]':
					delete_mark.append([kk,jj])
	return delete_mark

def find_sub_set(child,id_set,class_name):
	if child.find_elements_by_class_name(class_name)!=[]:
		id_tmp=[]
		text_tmp=[]
		for ll in child.find_elements_by_class_name(class_name):
			if len(ll.text)>0:
				if ll.id not in id_set:
					id_set.add(ll.id)
					#print(ll.id)
					text_tmp.append(ll.text)
					id_tmp.append(ll.id)
		return text_tmp,id_tmp,id_set
	else:
		return [],[],id_set

###判断回comment_order中对应回最上级的comment是什么 并重新组合
def find_top_item(comment_order,id_order,title):
	new_title_order=[]
	new_title_id_order=[]
	for i in range(len(comment_order)):
		second_order=comment_order[i][0]
		###找出其id
		second_id=id_order[i][0]
		###根据id找出上一级的title
		first_mark=0
		for j in range(1,len(title)):
			if second_id==title[j][1]:
				first_order=title[j-1][0]
				first_id=title[j-1][1]
				first_mark=1
		if first_mark==1:
			new_title_order.append([first_order]+comment_order[i])
			new_title_id_order.append([first_id]+id_order[i])
		else:
			new_title_order.append(comment_order[i])
			new_title_id_order.append(id_order[i])
	return new_title_order,new_title_id_order
###make the final title list
def make_up_whole_list(new_title_order,new_title_id_order,title):
	title_sum=[]
	id_sum=[]
	global mark
	for title_tmp in title:
		title_tmp_id=title_tmp[1]
		mark=3
		for i in range(len(new_title_id_order)):
			if title_tmp_id==new_title_id_order[i][0]:
				title_sum.append(new_title_order[i])
				id_sum.append(new_title_id_order[i])
				#print('add the group of '+str(title_tmp_id))
				mark=1
				break
			elif title_tmp_id in new_title_id_order[i][1:]:
				#title.append(new_title_order[i])
				#print(str(title_tmp_id) +' cannot find')
				mark=2
				break
		if mark==3:
			title_sum.append(title_tmp[0])
			id_sum.append(title_tmp_id)
			#print('add the content of '+str(title_tmp_id))
	return title_sum,id_sum

def create_table2(browser):
	title = browser.find_elements_by_class_name("note_content_title")
	title = [(k.text,k.id) for k in title if k.text!='']
	children = browser.find_elements_by_class_name("children")
	#note_panel = browser.find_elements_by_class_name("panel")
	author = browser.find_elements_by_class_name("signatures")
	author = [(k.text,k.id) for k in author if k.text!='']
	date = browser.find_elements_by_class_name("date")
	date = [(k.text,k.id) for k in date if k.text!='']
	contents0 = browser.find_elements_by_class_name("note_contents")
	contents = [(k.text,k.id) for k in contents0 if k.text!='' and \
	(k.text[:8]=='Comment:'  or  k.text[:7]=='Review:' or \
		k.text[:11]=='Metareview:'  or k.text[:24]=='Withdrawal Confirmation:' or k.text[:21]=='Desk Reject Comments:')]
	###Rating
	content_with_rating= [(k.text,k.id) for i,k in enumerate(contents0) if k.text!='' and \
	(k.text[:8]=='Comment:'  or  k.text[:7]=='Review:' or k.text[:7] == "Rating:"  or \
		k.text[:11]=='Metareview:'  or k.text[:24]=='Withdrawal Confirmation:' or k.text[:21]=='Desk Reject Comments:')]
	rating = [[x[0].split(":")[1],x[1],i,''] for  i,x in enumerate(content_with_rating) if x[0][:7] == "Rating:"]
	#confidence = [[x[0].split(":")[0],x[1],i,''] for  i,x in enumerate(content_with_confidence) if x[0][:11] == "Confidence:"]
	####找出其id和该rating内容的id
	####2019年和其他不一样，19年的rating在review后面，所以往前-1取
	for ii in range(len(rating)):
		confidence_idx=rating[ii][2]
		if confidence_idx+1<len(content_with_rating):
			if content_with_rating[confidence_idx-1][0][:7]=='Review:':
				rating[ii][3]=content_with_rating[confidence_idx-1][1]
			elif content_with_rating[confidence_idx+1][0][:7]=='Review:':
				rating[ii][3]=content_with_rating[confidence_idx+1][1]
		else:
			if content_with_rating[confidence_idx-1][0][:7]=='Review:':
				rating[ii][3]=content_with_rating[confidence_idx-1][1]
	####confidence  找出confidence的文本后，找出其id和该评论内容的id
	content_with_confidence= [(k.text,k.id) for i,k in enumerate(contents0) if k.text!='' and \
	(k.text[:8]=='Comment:'  or  k.text[:7]=='Review:' or k.text[:11] == "Confidence:"  or \
		k.text[:11]=='Metareview:'  or k.text[:24]=='Withdrawal Confirmation:' or k.text[:21]=='Desk Reject Comments:')]
	confidence = [[x[0].split(":")[1],x[1],i,''] for  i,x in enumerate(content_with_confidence) if x[0][:11] == "Confidence:"]
	####找出其id和该评论内容的id
	for ii in range(len(confidence)):
		confidence_idx=confidence[ii][2]
		if content_with_confidence[confidence_idx-1][0][:11]=='Metareview:' or content_with_confidence[confidence_idx-1][0][:7]=='Review:' or\
		 content_with_confidence[confidence_idx-1][0][:24]=='Withdrawal Confirmation:'\
		 or content_with_confidence[confidence_idx-1][0][:8]=='Comment:' or content_with_confidence[confidence_idx-1][0][:21]=='Desk Reject Comments:' :
			confidence[ii][3]=content_with_confidence[confidence_idx-1][1]
		elif content_with_confidence[confidence_idx-2][0][:11]=='Metareview:' or content_with_confidence[confidence_idx-2][0][:7]=='Review:' or\
		 content_with_confidence[confidence_idx-2][0][:24]=='Withdrawal Confirmation:'\
		 or content_with_confidence[confidence_idx-2][0][:8]=='Comment:' or content_with_confidence[confidence_idx-2][0][:21]=='Desk Reject Comments:' :
			confidence[ii][3]=content_with_confidence[confidence_idx-2][1]
	id_set=set()
	comment_order=[]
	comment_id_order=[]
	author_order=[]
	author_id_order=[]
	date_order=[]
	date_id_order=[]
	content_order=[]
	content_id_order=[]
	for child in children:
		if child.id not in id_set:
			id_set.add(child.id)
			comment_tmp,comment_id_tmp,id_set=find_sub_set(child,id_set,'note_content_title')
			author_tmp,author_id_tmp,id_set=find_sub_set(child,id_set,'signatures')
			date_tmp,date_id_tmp,id_set=find_sub_set(child,id_set,'date')
			contents_tmp,contents_id_tmp,id_set=find_sub_set(child,id_set,'note_contents')
			if len(comment_tmp)>0:
				comment_order.append(comment_tmp)
				comment_id_order.append(comment_id_tmp)
			if len(author_tmp)>0:
				author_order.append(author_tmp)
				author_id_order.append(author_id_tmp)
			if len(date_tmp)>0:
				date_order.append(date_tmp)
				date_id_order.append(date_id_tmp)
			if len(contents_tmp)>0:
				content_order.append(contents_tmp)
				content_id_order.append(contents_id_tmp)
	new_title_order,new_title_id_order=find_top_item(comment_order,comment_id_order,title)
	new_author_order,new_author_id_order=find_top_item(author_order,author_id_order,author)
	new_date_order,new_date_id_order=find_top_item(date_order,date_id_order,date)
	new_content_order,new_content_id_order=find_top_item(content_order,content_id_order,contents)
	title_sum,title_id_sum=make_up_whole_list(new_title_order,new_title_id_order,title)
	author_sum,author_id_sum=make_up_whole_list(new_author_order,new_author_id_order,author)
	date_sum,date_id_sum=make_up_whole_list(new_date_order,new_date_id_order,date)
	content_sum,content_id_sum=make_up_whole_list(new_content_order,new_content_id_order,contents)
	#####title那些包括题目在0下标  去除
	title_sum=title_sum[1:]
	author_sum=author_sum[1:]
	date_sum=date_sum[1:]
	#####let confidence has same length
	confidence_new=[]
	for j in range(len(content_id_sum)):
	    mark_confidence=0
	    if type(content_id_sum[j])==str:
	        for i in range(len(confidence)):
	            if content_id_sum[j]==confidence[i][3]:
	                confidence_new.append(str.strip(confidence[i][0]))
	                mark_confidence=1
	                break
	        if mark_confidence!=1:
	            confidence_new.append(None)
	    else:
	        confidence_tmp=[]
	        for sub_content_id in  content_id_sum[j]:
	            mark_confidence=0
	            for i in range(len(confidence)):
	                if sub_content_id==confidence[i][3]:
	                    confidence_tmp.append(str.strip(confidence[i][0]))
	                    mark_confidence=1
	                    break
	            if mark_confidence!=1:
	                confidence_tmp.append(None)
	        confidence_new.append(confidence_tmp)
	####let rating has same length
	rating_new=[]
	for j in range(len(content_id_sum)):
	    mark_confidence=0
	    if type(content_id_sum[j])==str:
	        for i in range(len(rating)):
	            if content_id_sum[j]==rating[i][3]:
	                rating_new.append(str.strip(rating[i][0]))
	                mark_confidence=1
	                break
	        if mark_confidence!=1:
	            rating_new.append(None)
	    else:
	        rating_tmp=[]
	        for sub_content_id in  content_id_sum[j]:
	            mark_confidence=0
	            for i in range(len(rating)):
	                if sub_content_id==rating[i][3]:
	                    rating_tmp.append(str.strip(rating[i][0]))
	                    mark_confidence=1
	                    break
	            if mark_confidence!=1:
	                rating_tmp.append(None)
	        rating_new.append(rating_tmp)
	return title_sum,author_sum,date_sum,content_sum,confidence_new,rating_new

with open('url_2019_1.txt') as f:
    urls_2019 = f.readlines()
urls_2019 = [url.strip() for url in urls_2019]
urls_2019[0]=urls_2019[0].replace('\ufeff','')

from pyvirtualdisplay import Display
display = Display(visible=0, size=(800, 800))  
display.start()
browser = webdriver.Chrome()
####产生两个表，第一个表
###字段 paperid,title, abstract, keyword, rating, url, withdrawn, decision
#第一个表
###字段 paperid,title, abstract, keyword, rating, url, withdrawn, decision
first_table=[]
second_table=[]
wait_time=0.1
max_try=15
commentid=0
fail_url=[]
for i, urls_this_year in enumerate(urls_2019):
	try:
	    browser = webdriver.Chrome()
	    browser.get(urls_this_year)
	    time.sleep(wait_time)
	    #last_index=browser.find_elements_by_class_name("permalink-button")[0].get_attribute('data-permalink-url').find('&')
	    #urls_this_year=browser.find_elements_by_class_name("permalink-button")[0].get_attribute('data-permalink-url')[0:last_index]
	    key = browser.find_elements_by_class_name("note_content_field")
	    key = [k.text for k in key]
	    withdrawn = 'Withdrawal Confirmation:' or 'Withdrawal:' in key
	    value = browser.find_elements_by_class_name("note_content_value")
	    value = [v.text for v in value]
	    # title
	    title = string.capwords(browser.find_element_by_class_name("note_content_title").text)
	    # abstract
	    valid = False
	    tries = 0
	    while not valid:
	        if 'Abstract:' in key:
	            valid = True
	        else:
	            time.sleep(wait_time)
	            tries += 1
	            key = browser.find_elements_by_class_name("note_content_field")
	            #print(key.id)
	            key = [k.text for k in key]
	            withdrawn = 'Withdrawal Confirmation:' in key
	            value = browser.find_elements_by_class_name("note_content_value")
	            value = [v.text for v in value]                        
	            if tries >= max_try:
	                print('Reached max try: {} ({})'.format(title, urls_this_year))
	                break
	    abstract = ' '.join(value[key.index('Abstract:')].split('\n'))
	    # keyword
	    if 'Keywords:' in key:
	        keyword = value[key.index('Keywords:')].split(',')
	        keyword = [k.strip(' ') for k in keyword]
	        keyword = [''.join(string.capwords(k).split(' ')) for k in keyword if not k == '']
	        for j in range(len(keyword)):
	            if '-' in keyword[j]:
	                keyword[j] = ''.join([string.capwords(kk) for kk in keyword[j].split('-')])       
	    else:
	        keyword = []
	    # rating
	    rating_idx = [i for i, x in enumerate(key) if x == "Rating:"]
	    rating = []
	    if len(rating_idx) > 0:
	        for idx in rating_idx:
	            rating.append(int(value[idx].split(":")[0]))
	    ###metareview confidence
	    metareview = 'Metareview:' in key
	    if metareview:
	        try:
	            metareview_confidence=int(value[key.index('Metareview:')+1].split(":")[0])
	        except:
	    	    metareview_confidence=int(value[key.index('Metareview:')+2].split(":")[0])
	    else:
	    	metareview_confidence=None
	    # confidence
	    confidence_idx = [i for i, x in enumerate(key) if x == "Confidence:"]
	    confidence = []
	    if len(confidence_idx) > 0:
	        for idx in confidence_idx:
	            confidence.append(int(value[idx].split(":")[0]))
	    ####if  metareview, confidence will include metareview's confidence, we should remove it
	    if metareview:
	        try:
	            confidence.remove(metareview_confidence)
	        except Exception as e:
	        	print(e)
	        	print(confidence)
	        	print(metareview_confidence)
	        	print(urls_this_year)
	        	print('this url fail to find metareview_confidence')
	    if len(confidence)!=len(rating):
	    	print('confidence and rating not equal')
	    	print(urls_this_year)
	    	confidence+=1###let this url wrong
	    # decision
	    if 'Recommendation:' in key:
	        decision = value[key.index('Recommendation:')]
	    elif 'Decision:' in key:
	        decision = value[key.index('Decision:')]
	    else:
	        decision = 'N/A'
	    print('[{}] [Abs: {} chars, keywords: {}, ratings: {}, decision: {}] {}'.format(
	        i+1, len(abstract), len(keyword), rating, decision, title))
	    #first_table.append((i+1,title, abstract, keyword, rating, urls_this_year, withdrawn, decision))
	    title_sum_t2,author_sum_t2,date_sum_t2,content_sum_t2,confidence_new2,rating_new2=create_table2(browser)
	    delete_set=find_delete(author_sum_t2)
	    row_mark=-999
	    for delete_index in delete_set:
	        if type(delete_index)==int:
	            date_sum_t2.insert(delete_index,'')
	            content_sum_t2.insert(delete_index,'')
	            confidence_new2.insert(delete_index,None)
	            rating_new2.insert(delete_index,None)
	        elif (author_sum_t2[delete_index[0]]==list(['[Deleted]']*len(author_sum_t2[delete_index[0]])) or author_sum_t2[delete_index[0]][0]=='[Deleted]') \
	        and row_mark!=delete_index[0]:
	            date_sum_t2.insert(delete_index[0],['']*len(author_sum_t2[delete_index[0]]))
	            content_sum_t2.insert(delete_index[0],['']*len(author_sum_t2[delete_index[0]]))
	            confidence_new2.insert(delete_index[0],[None]*len(author_sum_t2[delete_index[0]]))
	            rating_new2.insert(delete_index[0],[None]*len(author_sum_t2[delete_index[0]]))
	            row_mark=delete_index[0]
	        else:
	            if type(date_sum_t2[delete_index[0]])==list:
	                date_sum_t2[delete_index[0]].insert(delete_index[1],'')
	                content_sum_t2[delete_index[0]].insert(delete_index[1],'')
	                confidence_new2[delete_index[0]].insert(delete_index[1],None)
	                rating_new2[delete_index[0]].insert(delete_index[1],None)
	            else:
	                date_tmp0=[]
	                date_tmp0.append(date_sum_t2[delete_index[0]])
	                date_sum_t2[delete_index[0]]=date_tmp0
	                #date_sum_t2[delete_index[0]]=list(date_sum_t2[delete_index[0]])
	                date_sum_t2[delete_index[0]].insert(delete_index[1],'')
	                content_tmp0=[]
	                content_tmp0.append(content_sum_t2[delete_index[0]])
	                content_sum_t2[delete_index[0]]=content_tmp0
	                #content_sum_t2[delete_index[0]]=list(content_sum_t2[delete_index[0]])
	                content_sum_t2[delete_index[0]].insert(delete_index[1],'')
	                if confidence_new2[delete_index[0]] is not None:
	                    confidence_new2[delete_index[0]]=list(confidence_new2[delete_index[0]])
	                    confidence_new2[delete_index[0]].insert(delete_index[1],None)
	                else:
	                    confidence_new2[delete_index[0]]=[None]
	                    confidence_new2[delete_index[0]].insert(delete_index[1],None)
	                #confidence_new2[delete_index[0]]=list(confidence_new2[delete_index[0]])
	                #confidence_new2[delete_index[0]].insert(delete_index[1],'')
	                if rating_new2[delete_index[0]] is not None:
	                    rating_new2[delete_index[0]]=list(rating_new2[delete_index[0]])
	                    rating_new2[delete_index[0]].insert(delete_index[1],None)
	                else:
	                    rating_new2[delete_index[0]]=[None]
	                    rating_new2[delete_index[0]].insert(delete_index[1],None)
	    paper_id=i+1
	    for k in range(len(title_sum_t2)):
	        if type(title_sum_t2[k])==str:
	            commentid+=1
	            if ('Chair' in title_sum_t2[k] or 'Reviewer' in title_sum_t2[k] or 'Reviewer' in author_sum_t2[k] or 'Chair' in author_sum_t2[k]) and 'Reply' not in title_sum_t2[k]:
	            	is_offical=True
	            else:
	            	is_offical=False
	            if content_sum_t2==[]:
	                second_table.append((commentid,paper_id,None,title_sum_t2[k],author_sum_t2[k],date_sum_t2[k],'',is_offical,confidence_new2[k],rating_new2[k]))
	            else:
	                second_table.append((commentid,paper_id,None,title_sum_t2[k],author_sum_t2[k],date_sum_t2[k],content_sum_t2[k],is_offical,confidence_new2[k],rating_new2[k]))
	        else:
	            for t in range(len(title_sum_t2[k])):
	                commentid+=1
	                if ('Chair' in title_sum_t2[k][t] or 'Reviewer' in title_sum_t2[k][t] or 'Reviewer' in author_sum_t2[k][t] or 'Chair' in author_sum_t2[k][t]) \
	                and 'Reply' not in title_sum_t2[k][t] and 'Authors' not in author_sum_t2[k][t] :
	                    is_offical=True
	                else:
	                    is_offical=False
	                if t==0:
	                    if rating_new2[k] is None:
	                        second_table.append((commentid,paper_id,None,title_sum_t2[k][t],author_sum_t2[k][t],date_sum_t2[k][t],content_sum_t2[k][t],is_offical,None,None))
	                    else:
	                        second_table.append((commentid,paper_id,None,title_sum_t2[k][t],author_sum_t2[k][t],date_sum_t2[k][t],content_sum_t2[k][t],is_offical,confidence_new2[k][t],rating_new2[k][t]))
	                else:
	                    if rating_new2[k] is None:
	                        second_table.append((commentid,paper_id,int(commentid-1),title_sum_t2[k][t],author_sum_t2[k][t],date_sum_t2[k][t],content_sum_t2[k][t],is_offical,None,None))
	                    else:
	                        second_table.append((commentid,paper_id,int(commentid-1),title_sum_t2[k][t],author_sum_t2[k][t],date_sum_t2[k][t],content_sum_t2[k][t],is_offical,confidence_new2[k][t],rating_new2[k][t]))
	    first_table.append((i+1,title, abstract, keyword,metareview_confidence,confidence, rating, urls_this_year, withdrawn, decision))
	    browser.quit()
	except Exception as e:
	    print(e)
	    print('Failed to load {}'.format(urls_this_year))
	    fail_url.append(urls_this_year)
#####
try:
	browser.quit()
except Exception as e:
	print('cannot browser quit')
	print(e)
display.stop() 
pd.set_option('precision', 0)
first_table_df=pd.DataFrame(first_table)
first_table_df.columns=['paperid','title', 'abstract', 'keyword','metareview_confidence','confidence' ,'rating', 'url','withdrawn', 'decision']
first_table_df.to_csv("/home/yiyang/xlq/openreview/first_table_df_2019_v5.csv",index=False,sep=',')
second_table_df=pd.DataFrame(second_table)
second_table_df.columns=['commentid','paperid','last_commentid','comement_title','author','date','content','is_offical','confidence','rating']
second_table_df.to_csv("/home/yiyang/xlq/openreview/second_table_df_2019_v5.csv",index=False,sep=',')
####save fail url
print(fail_url)
output = open('fail_url_2019_v5.pkl', 'wb')
pickle.dump(fail_url, output)


'''
####更改is official
def offical(x):
    if ('Chair' in x['comement_title'] or 'Reviewer' in x['comement_title'] or 'Chair' in x['author'] or 'Reviewer' in x['author'])\
    and 'Reply' not in x['comement_title'] and 'Authors' not in x['author']:
        return True
    else:
        return False
second_table_df_2019['is_offical']=second_table_df_2019.apply(lambda x: offical(x),axis=1)


def list2int(x):
    if pd.isnull(x['confidence']) is True:
        return x['confidence']
    if len(str(x['confidence']))==1:
        #print(x['confidence'])
        return x['confidence']
    else:
        print(x['confidence'])
        return x['confidence'].split(',')[0].replace('[','')
second_table_df_2019[["confidence"]]=second_table_df_2019.apply(lambda x:list2int(x),axis=1)

def list2int_rating(x):
    if pd.isnull(x['rating']) is True:
        return x['rating']
    if len(str(x['rating']))==1:
        #print(x['confidence'])
        return x['rating']
    else:
        print(x['rating'])
        return x['rating'].split(',')[0].replace('[','')
second_table_df_2019[["rating"]]=second_table_df_2019.apply(lambda x:list2int_rating(x),axis=1)
'''