grep -E 'CHROM|DEL' merge.bed > merge.DEL.bed
grep -E 'CHROM|INS' merge.bed > merge.INS.bed

intersect merge.DEL.bed consensus.DEL.bed > merge.DEL.shared.bed
intersect merge.INS.bed consensus.INS.bed > merge.INS.shared.bed
intersect merge.INS.bed consensus.MEI.bed > merge.INS.shared.bed
intersect ./Paragraph/DEL/genotypes.bed consensus.DEL.bed > paragraph.DEL.shared.bed
intersect ./Paragraph/INS/genotypes.bed consensus.INS.bed > paragraph.INS.shared.bed
intersect ./Paragraph/INS/genotypes.bed consensus.MEI.bed > paragraph.INS.shared.bed

#intersect merge.DEL.bed ./Paragraph/DEL/genotypes.bed > merge.DEL.shared.bed
#intersect merge.INS.bed ./Paragraph/INS/genotypes.bed > merge.INS.shared.bed
#intersect ./Paragraph/DEL/genotypes.bed merge.DEL.bed -v > paragraph.DEL.not.bed
#intersect ./Paragraph/INS/genotypes.bed merge.INS.bed -v > paragraph.INS.not.bed
#intersect ./Paragraph/DEL/genotypes.bed merge.DEL.bed > paragraph.DEL.shared.bed
#intersect ./Paragraph/INS/genotypes.bed merge.INS.bed > paragraph.INS.shared.bed

echo "######################## Deletions #############################"

echo "======================== Paragraph ============================="
tabulate.sh paragraph.DEL.shared.bed
verify.sh $1
wc -l *_as_*.bed

echo "========================== Nebula =============================="
tabulate.sh merge.DEL.shared.bed 
verify.sh $1
wc -l *_as_*.bed

#echo "====================== Only Paragraph =========================="
#tabulate.sh paragraph.DEL.not.bed
#verify.sh $1
#wc -l *_as_*.bed

echo "######################## Insertions ############################"

echo "========================= Paragraph ============================"
tabulate.sh paragraph.INS.shared.bed
verify.sh $1
wc -l *_as_*.bed

echo "========================== Nebula =============================="
tabulate.sh merge.INS.shared.bed 
verify.sh $1
wc -l *_as_*.bed

#echo "====================== Only Paragraph =========================="
#tabulate.sh paragraph.INS.not.bed
#verify.sh $1
#wc -l *_as_*.bed
