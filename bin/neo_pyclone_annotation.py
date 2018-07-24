#!/usr/bin/python
# -*- coding: UTF-8 -*-
###########process varscan result into pyclone input#########
import pandas as pd
import numpy as np
import sys,getopt

opts,args=getopt.getopt(sys.argv[1:],"hn:i:s:c:o:S:C:t:",["neoantigen_file","vep_input_file","pyclone_loci","out_dir","SampleID","cancer_type"])
neoantigen_file=""
vep_input_file=""
pyclone_loci=""
output_dir=""
sample_id=""
cancer_type=""
USAGE='''usage: python pyclone_input.py -n <neoantigen_file> -i <vep_input_file> -s <pyclone_loci> -o <outdir> -S <sample_id> -t <cancer_type> [option]"
		required argument:
			-n | --neoantigen_file: 
			-i | --vep_input_file : snv vep input file
			-s | --pyclone_loci : pyclone_loci file result from pyclone
			-o | --out_dir : output_directory
			-S | --SampleID : sample id
			-t | --cancer_type : specify cancer type
'''
for opt,value in opts:
	if opt =="h":
		print USAGE
		sys.exit(2)
	elif opt in ("-n","--neoantigen_file"):
		neoantigen_file=value
	elif opt in ("-i","--vep_input_file"):
		vep_input_file=value
	elif opt in ("-s","--pyclone_loci"):
		pyclone_loci=value
	elif opt in ("-o","--out_dir"):
		out_dir=value  
	elif opt in ("-S","--SampleID"):
		sample_id=value
	elif opt in ("-t","--cancer_type"):
		cancer_type=value

#print coverage
if (neoantigen_file=="" or vep_input_file=="" or pyclone_loci=="" or out_dir=="" or sample_id=="" or cancer_type==""):
	print USAGE
	sys.exit(2)
gene_normal_expression_dic={}
gene_dic={}	
vep_pos_list=[]
vep_gene_list=[]
f_vep=open(vep_input_file)
for ele in f_vep:
	if ele.startswith('#'):
		continue
	else:
		vep_pos=ele.strip().split('\t')[1]
		extra=ele.strip().split('\t')[-1]
		#vep_gene=extra.split(';')[2].split('=')[1]
		element=extra.split(';')
		for ele in element:
			sub_ele=ele.split('=')
			if sub_ele[0]=="SYMBOL":
				vep_gene=sub_ele[1]
	if vep_gene not in vep_gene_list:
		vep_pos_list.append(vep_pos)
		vep_gene_list.append(vep_gene)

f_vep.close()
#print len(vep_pos_list),len(vep_gene_list)
for i in range(len(vep_pos_list)):
	gene_dic[vep_gene_list[i]]=vep_pos_list[i]
gene_normal_expression_dic={}
data_gtex=pd.read_table('/home/zhouchi/database/Annotation/expression/GTEx_Analysis_v6p_RNA-seq_RNA-SeQCv1.1.8_gene_median_rpkm.gct',header=0,sep='\t')
expression_gene=data_gtex.Description
data_exp=data_gtex.iloc[:,[4,22,26,27,29,35,36,37,40,41,42,44,46,49,50,51,52,54]]
data_exp.columns="Adrenal Gland","Breast","Cervix","Colorectal","Esophagus","Kidney","Liver","Lung","Nervous System","Ovary","Pancreas","Prostate","Skin","Stomach","Testis","Thyroid","Uterus","Blood"
f=lambda x:x*1000000/sum(x)
data_tpm=data_exp.apply(f)
normal_expression=data_tpm[cancer_type]
for i in range(len(expression_gene)):
	gene_normal_expression_dic[expression_gene[i]]=normal_expression[i]

#print gene_dic,len(gene_dic)
#gene_name=[]
#for ele in open(neoantigen_file,'r'):
#	if ele.startswith('#'):
#		continue
#	else:
#		gene=ele.strip().split('\t')[1]
#		gene_name.append(gene)
data_neo=pd.read_table(neoantigen_file,header=0,sep='\t')
#print data_neo
gene_name=data_neo.Gene


pos_cp_dic={}
pos_vaf_dic={}
#pyclone_pos=[]
#cellular_prevalence_list=[]
#variant_allele_frequency_list=[]
for ele in open(pyclone_loci,'r'):
	if ele.startswith('mutation_id'):
		continue
	else:
		line=ele.strip().split('\t')
		chr_name=line[0].split(':')[2]
		pos=line[0].split(':')[3]
		chr_pos=chr_name+':'+pos
		cellular_prevalence=line[3]
		vaf=line[5]
	pos_cp_dic[chr_pos]=cellular_prevalence
	pos_vaf_dic[chr_pos]=vaf
	#pyclone_pos.append(chr_pos)
	#cellular_prevalence_list.append(cellular_prevalence)
	#variant_allele_frequency_list.append(vaf)

cellular_prevalence_neo=[]
variant_allele_frequency_neo=[]
neo_normal_expression_list=[]
for ele in gene_name:
	neo_pos=gene_dic[ele]
	if ele in gene_normal_expression_dic.keys():
		neo_normal_expression=gene_normal_expression_dic[ele]
	else:
		neo_normal_expression=0
	c_p=pos_cp_dic[neo_pos]
	v_a_f=pos_vaf_dic[neo_pos]

	cellular_prevalence_neo.append(c_p)
	variant_allele_frequency_neo.append(v_a_f)
	neo_normal_expression_list.append(neo_normal_expression)
data_neo["cellular_prevalence"]=cellular_prevalence_neo
data_neo["variant_allele_frequency"]=variant_allele_frequency_neo
data_neo[cancer_type]=neo_normal_expression_list
#del data_neo["Gene Name"]
del data_neo["cleavage_prediction_score"]
del data_neo["tap_prediction_score"]
#print data_neo
data_fill_na=data_neo.fillna(0)
####HLA:0201 and sort by aff_rank
data_drop=data_fill_na.drop_duplicates(subset=["Gene","MT_pep","WT_pep"])
data_sort=data_drop.sort_values(["MT_Binding_Aff"],ascending=True)
#print data_sort
data_sort.to_csv(out_dir+'/'+sample_id+'_pyclone_neo.txt',header=1,sep='\t',index=0)





