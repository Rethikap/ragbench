# Blind calibration sheet

40 answers sampled across all configurations. The configuration is not
shown, and the items are shuffled so the order does not reveal it.

Score each item in `calibration_scores.csv` on three 1-5 scales and one verdict:

- **faithfulness** -- is every claim supported by the RETRIEVED PASSAGES? A value
  that appears in the passages but is attached to the wrong entity is not faithful.
- **relevance** -- does it answer the question that was asked?
- **completeness** -- does it cover what the reference answer covers?
- **verdict** -- one of: correct, partially_correct, incorrect, abstained.

Leave all four blank for an item you would rather not score; blank rows are
skipped rather than counted as disagreement. For an abstention, set the verdict
and leave the three scales blank.

---

## 1. `62a3df05`

**Question.** Which periodontal pathogen was confirmed by PCR among the live bacteria found in mouse brains, and what did that finding support?

**Reference answer.** F. nucleatum; its presence supports the concept of a natural living microbial presence in the brains of mice, that is, a natural brain microbiome.

**Answer under review.**

> F. nucleatum was confirmed by PCR among the live bacteria found in mouse brains, and that finding supported the concept of a natural brain microbiome and the presence of periodontal pathogens in the brain.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
um in AD pathology may be similar to that of its role in dental plaque formation, that is, it may act as a "microbial bridge" to communicate with other bacteria.

Importantly, in a slightly different oral infection mouse model, we found the presence of whole live oral bacteria present in fresh mouse brains from both control and infected mice (Additional file 2: Figure S2). Furthermore, we used PCR validation to confirm that one of the live bacteria present in the brains, included a periodontal pathogen, namely, F. nucleatum. This speaks to the idea of a natural living microbial presence in the brains of mice and supports the concept of a natural brain microbiome.

In addition to individual bacteria, dysbiosis can also contribute to AD pathogenesis. Gut and oral dysbiosis have been implicated in AD development and progression [, –]. However, there is no direct evidence supporting a correlation between alterations in the microbial profile of the oral cavity and AD brain. Using 16s rRNA sequencing, we found that the microbiome composition of the brain of the periodontally infected mice was significantly different from that of the control mice. The relative abundance of Firmicutes and Proteobacteria was significantly higher in the brain after polymicrobial–periodontal infection, and the proportions of Actinobacteria, Bacteroidetes and Cyanobacteria were much lower. These altered dominant phyla may not possess periodontal pathogenicity, and may not originate from the oral cavity, but these changes could be the result of oral microbial alterations. Therefore, periodontal infection may not only lead to the transfer of periodontal pathogens from oral cavity to brain, but more importantly, it may also contribute to changes in the microbiome composition of the brain. The potential for a periodontal infection to promote an increase in brain pro-inflammatory cytokines, including IL-1β, IL-6 and TNF-α, which ultimately promote the production of Aβ and hyperphosphorylation of tau, resulting in neurodegeneration and AD has been postulated. Therefore, restoring the composition of the oral microbiome could be a helpful approach and possible therapeutic intervention strategy for AD. Recently, our group demonstrated that nisin can prevent and disrupt oral biofilms, decrease the amount of oral pathogens within oral biofilms, and return the diversity and composition of diseases-associated

s the periodontal pathogen burden in the brain following oral polymicrobial infection/periodontal disease

To further assess the presence of periodontal bacteria in the brain tissues, the number of periodontal pathogens was measured in the brain samples using RT-PCR in a manner of absolute quantification. The detection frequency of the four periodontal pathogens is shown in Fig. 3A. P. gingivalis could be detected in all four groups with different frequencies. T. forsythia was detected in the infection, nisin, and nisin + infection group, but not in the control group. F. nucleatum was detected in the infection, nisin + infection group, but not in the control and nisin group. The presence of T. denticola was not detected in any of the groups. The copy number for P. gingivalis in the control group was significantly lower than that in the infection group (P < 0.05) (Fig. 3B). Although the P. gingivalis copy number was lower in the infection + nisin group than in the infection group, this did not reach statistical significance (Fig. 3B). However, nisin treatment significantly reduced the T. forsythia copy number in the infection + nisin group compared to the infection group (P < 0.05) (Fig. 3C). Interestingly, the F. nucleatum levels were higher in the infection + nisin group than that in the infection group, but the difference was not statistically significant (Fig. 3D). When taken in aggregate, the copy numbers for T. forsythia were highest among all 4 pathogens in the infection group (Fig. 3E).

Using a slightly different mouse model with only a T. denticola infection and utilizing a sterile technique and environment, we were able to isolate whole living bacteria from the fresh brains of both control and infected mice. Using PCR validation we confirmed the presence of F. nucleatum in the fresh brains of the mice (Additional file 2: Fig. S2).

Oral polymicrobial infection/periodontal disease induces neuroinflammation in the brain and nisin reverses the change

To evaluate the ability of an oral polymicrobial infection to induce inflammation in the brain and the ability of nisin to relieve this neuroinflammation, we performed gene expression analysis to evaluate the immune cytokine profiles

v) CMC in PBS, and this mixture was used as the polymicrobial oral inoculum.

Furthermore, we quantified the concentration of all four bacteria, ensuring a concentration of 2.5 × 108 four periodontal pathogens (P. gingivalis, T. denticola, T. forsythia, and F. nucleatum) and the purity and viability of the four bacteria were confirmed by microscopic evaluation and colony morphology prior to inoculation. Finally, we’ve shown in this very mouse model at the end of the experimental period after euthanasia that these bacteria are all present locally in the gingiva of the mice and that they mount a systemic antibody response to each pathogen, indicating the viability of each pathogen in the inoculation step. Although, we have found that it is relatively hard for T. denticola to colonize the oral cavity compared with the other three bacteria, we have cultured T. denticola strictly according to our typical protocols (3234-40), and third and fifth passage T. denticola preparations were used in this experiment.

Nisin preparation

An ultra-pure (> 95%) food grade form of nisin Z (NisinZ® P) was purchased from Handary (S.A., Brussels, Belgium), a primary manufacturer of nisin in the food industry. The nisin stock solution was prepared at a concentration of 600 μg/ml in sterile Milli-Q filtered water, that was further filtered using a 0.22 μm syringe filter, and stored at 4 ℃ for a maximum of 5 days for use in experiments. For oral treatment of mice, the nisin solution was then mixed with an equal volume of sterile 4% CMC and adjusted to the final concentration of 300 μg/ml.

DNA isolation from brain tissues

DNA was extracted from the mouse brain tissues to evaluate microbiological changes following periodontal bacterial challenge and/or nisin treatment using real-time polymerase chain reaction (PCR) and 16s rRNA sequencing. DNA was isolated and purified using the QIAamp® DNA Mini kit (Qiagen, Hilden, Germany) as in our previous study. The isolated DNA was stored at − 20 °C until further processing for real-time PCR and 16s rRNA sequencing analysis.

RNA isolation from brain tissues

For RNA stabilization, the mouse brain tissues were treated immediately after sample collection with an RNAlater

al pathogens, such as Porphyromonas gingivalis and Treponema species, have been found in post-mortem brain tissues of AD patients. In addition, animal studies have been conducted to determine the effects of periodontitis on pathogen translocation and possible effects on the brain. Periodontal pathogens and their molecules have also been reported in the brain. Overall, these findings strengthen the hypothesis that periodontal pathogens play an important role in the development of AD. Periodontal disease and its characteristic oral microbial dysbiosis are thought to contribute to neuroinflammation and amyloid protein production via translocation of periodontal pathogens and their components to the brain. This hypothesis is further supported by research linking the presence of periodontal microorganisms with increased Amyloid β deposition, tau hyperphosphorylation, and glial cell inflammation and activation [–]. A recent study showed that treatment with a gingipain inhibitor reduced P. gingivalis infection in the brain of mice and prevented further neurodegeneration and accumulation of pathologic plaques, suggesting that controlling periodontal infections and microorganisms may be an effective way to slow down the development of AD.

Despite this compelling evidence for the presence of bacteria in the brain supporting the concept of a brain microbiome, there is considerable debate that a brain microbiome exists in healthy individuals. Currently the evidence for the infection of the brain in mouse studies is based on detection of bacterial products, including DNA, RNA, LPS and surface proteins, yet microbiome sequencing studies have not been performed. Here, we examine the presence of a brain microbiome using a genomic method-driven approach.

Nisin, a class I Lantibiotic bacteriocin produced by the probiotic Lactococcus lactis, has shown efficacy in treating a variety of infectious diseases, including gastrointestinal infections, respiratory tract infections, skin/soft tissue infections, and oral infectious diseases, including periodontal disease. In addition, we’ve demonstrated that nisin treatment can decrease the levels of gram negative periodontal pathogens in planktonic form and in oral biofilms and return their microbial diversity back to control ‘healthy’ levels [–]. Nisin can also prevent periodontal disease-related bone loss and inflammation while promoting reparative proliferation and a healthy microbiome. Therefore, the objective of this study
```

</details>

## 2. `c280db9c`

**Question.** What R-squared and p-value were reported for the linear regression between CSF GFAP and 18F-FDG brain uptake in BA9?

**Reference answer.** R2 = 0.1806, with F (1,27) = 5.069 and p = 0.0342.

**Answer under review.**

> The R-squared value was 0.1806 and the p-value was 0.0342 for the linear regression between CSF GFAP and 18F-FDG brain uptake in BA9.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
see Figure 1), with peaks in BA 6, 9 and 11 [see Table 2].

Moreover, a significant negative relationship between brain glucose consumption and CSF levels of β-S100 was also found in a wide cluster that included the left supramarginal gyrus, the inferior parietal lobe and middle temporal gyrus (see Figure 2), with peaks in Brodmann Areas 21 and 40 [see Table 3]. We did not find any significant relationships between 18F-FDG uptake and CSF levels of sTREM-2.

Lastly, we performed linear regression analyses to assess the association between glial CSF biomarkers and metabolism in the specific Broadman Areas of interest.

Figure 3a shows regressions between β-S100 and 18F-FDG brain uptake in BA40 (R2 = 0.1593, F (1,27) = 4.737, p = 0.0392), BA21 (R2 = 0.1440, F (1,27) = 4.207, p = 0.0509) and the widened cluster of the parietal lobe (R2 = 0.1460, F (1,27) = 4.275, p = 0.0492).

Figure 3b shows the linear regression between CSF GFAP and 18F-FDG brain uptake in BA9 (R2 = 0.1806, F (1,27) = 5.069, p = 0.0342), BA11 (R2 = 0.1705, F (1,27) = 4.727, p = 0.0402) and BA6 (R2 = 0.0313, F (1,27) = 0.9420, p = 0.3419).

4. Discussion

Despite its widespread use in both clinical settings and basic research, the identity of the cell types contributing to 18F-FDG-PET signal is still debated. Traditionally, 18F-FDG-PET signal has been attributed only to neuronal uptake, with hypometabolism being considered as a direct index of neuronal dysfunction—loss of neuropil, synapse, or functional impairment—or death. However, evaluating glucose consumption in AD is made complex by other additional factors, including changes in the expression of glucose transporters (GLUT)

org/index.html, accessed on 1 January 2023). As suggested by Bennett et al., sPM t-maps were calculated for multiple comparisons using the false discovery (p < 0.05) and corrected for multiple comparisons at the cluster level (p < 0.001).

The level of significance was set at 100 (5 × 5 × 5 voxels, i.e., 11 × 11 × 11 mm) contiguous voxels. The voxel-based analyses were performed in the subgroup of patients using regression analyses. We designed independent models assessing the effects of each CSF biomarker (levels of GFAP, sTREM-2 and βS100) as regression factors—independent variables—on cortical 18F-FDG uptake, using age and sex as covariates, as well as t-tau levels in order to adjust for another marker of neurodegeneration. Positive and negative associations were tested in all cases.

The cluster obtained in the regression analysis was then exported by means of the WFU Pickatlas tool implemented in SPM 12. Specifically, the mean signal intensities calculated from each cluster within each subject were normalized to the average intensities of the Pons volume of interest. The use of normalization based on activity in the pons, rather than whole-brain counts as in the reference region, has been reported to result in greater accuracy in discriminating patients from controls in neurodegenerative diseases. As previously suggested by Pagani and colleagues), a dataset of normalized 18F-FDG values relevant to the cluster under study was exported. To determine whether the normalized 18F-FDG values for the studied cluster were Gaussian distributed, the D’Agostino K-squared normality test was applied (with the null hypothesis being normal distribution). We then performed linear univariate regression analyses using GraphPad Prism© version 9.3.1 for Windows (GraphPad Software, San Diego, California USA, www.graphpad.com, accessed on 1 January 2023) to visualize significant findings, namely the association between CSF glial biomarkers and normalized continuous data representing metabolism in the specific Broadman Areas of interest.

3. Results

First, we retrieved a trend of positive association between 18F-FDG uptake and CSF levels of GFAP in the right frontal-medial and precentral gyri (

2 mL was used for routine biochemical analysis and we centrifuged the remaining 8 mL at 2000× g at +4 °C for 10 min and aliquoted them in 1 mL portions. The aliquots were frozen at −80 °C for further analysis of CSF, AD, and glial biomarkers. We used commercially available kits for biochemical analysis. CSF Aβ42, p-tau and t-tau concentrations were determined using a sandwich enzyme-linked immunosorbent assay (EUROIMMUN ELISA©), LUMINEX© Multiple assays ELISA was used for CSF GFAP and β-S100 concentrations.

Blood samples were also drawn in EDTA tubes. The DNA was extracted automatically and APOE genotyping was conducted by allelic discrimination technology with real-time PCR, according to the manufacturer’s instructions (TaqMan; Applied Biosystems).

2.3. 18F-FDG-PET Data Acquisition

All acquisitions were performed at the Nuclear Medicine Unit of the University Hospital “Policlinico Tor Vergata” in Rome with a General Electric VCT PET/CT scanner (GE Medical Systems, Tennessee, USA). All subjects fasted for at least 5 h before i.v. injection of FDG, and serum glucose levels were in range according to European Association of Nuclear Medicine guidelines. Patients were injected intravenously with 18F-FDG (dose range 185–295 MBq) and then hydrated with 500 mL of saline (0.9% sodium chloride), according to a previous similar report of our group in this field. The scan started 30 min after the injection and lasted ten minutes. Acquisition and reconstruction parameters are reported elsewhere and were followed according to the report cited above..

Upon imaging evaluation, all 27 subjects showed typical findings of brain cortical hypometabolism in key regions compatible with a diagnosis of classical AD (parietal and posterior cingulate cortices, precuneus, or a combination of the above).

2.4. Statistical Analysis

The relationship between levels of CSF GFAP, sTREM-2 and βS100 biomarkers and brain 18F-FDG uptake were analyzed through separate correlation models for each biomarker and direction, performed using Statistical parametric mapping (SPM) 12 (Wellcome Department of Cognitive Neurology, London, UK; https://www
```

</details>

## 3. `ff53963b`

**Question.** Which novel MHC-I partner does amyloid-beta-oligomer destabilisation of the synaptic MHC-I-beta2M complex impair the interaction with, and what reversed the resulting signalling impairment?

**Reference answer.** NCAM-1; inhibiting the amyloid-beta-induced destabilisation of the MHC-I complex with SCT reversed the neuronal signalling impairment.

**Answer under review.**

> The amyloid-beta-oligomer destabilization of the synaptic MHC-I-beta2M complex impairs the interaction with NCAM-1. This impairment was reversed by the stabilization of the MHC-I-beta2M complex using SCT, which also restored NCAM-1 signaling.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
Discussion

The present study revealed that Aβ oligomers destabilizes synaptic MHC-I-β2M complex, impairing the interaction with NCAM-1, a novel MHC-I partner. We here further showed that inhibiting the Aβ-induced destabilization of MHC-I complex by SCT can reverse the neuronal signaling impairment, harnessing a novel therapeutic strategy.

Although studies have been made about the role of neuronal MHC-I in synaptic plasticity, little was known about MHC-I function in neurological diseases. Especially, the connection between MHC-I function and its role in AD remained unclear, despite genetic analyses showing an increased frequency of some MHC-I alleles in individuals with AD. We here found that the unstable β2M-free MHC-I heavy chain was increased in AD brains (Fig. 2). The oligomeric Aβ was largely responsible for the destabilization of neuronal MHC-I-β2M complexes (Fig. 1). Aβ treatment caused MHC-I-β2M complex to degenerate into soluble β2M and β2M-free MHC-I heavy chain, leading to rapid internalization of MHC-I heavy chain followed by lysosomal degradation (Fig. 1). This β2M-free MHC-I heavy chain was also found to regulate synapse density negatively in glutamatergic neurons, which may be related with synapse loss in AD brains. MHC-I was also recently reported to be involved in the pathogenic mechanisms of the strongest risk factor of sporadic AD, apolipoprotein-E4.

Since NCAM1 is a novel interacting partner of neuronal MHC-I-β2M complex (Fig. 3) and MHC-I-β2M is destabilized by Aβ oligomers and in AD brains (Figs. 1, 2), we speculated that the interaction of NCAM1 with MHC-I-β2M complex is also deregulated. As expected, co-immunoprecipitation assay showed reduction in the amount of NCAM1-MHC-I-β2M complex in AD brains (Fig. 4A, B). In primary neurons, NCAM1 co-localized with MHC-I at the surface of the soma or dendrites, however Aβ oligomer reduced the co-localization intensity between MHC-I and NCAM1 or each protein levels (Fig. 4C–E). Aβ treatment reduced the amount of NCAM1 interacting with MHC-I by about 50% relative to control in primary neurons (Fig. 4F, G). Aβ treatment also reduced CREB phosphorylation, which is part of the final cascade of NCAM1 signaling (Fig. 4H, I), suggesting that the MHC-I–β2M complex is important for interacting with NCAM1 and activating its signaling. Together, these observations suggested that Aβ-mediated destabilization of MHC-I-β2M complex eventually impairs the formation of NCAM1-MHC-I-β2M complex, subsequently dysregulating NCAM1 signaling.

Stabilization of MHC-I-β2M complex rescued Aβ-mediated MHC-I depletion and dysregulation of NCAM1-MHC-I interactions

Because the structural formation of MHC-I-β2M complex is critical for interaction with its functional counterpart, we hypothesized that a conformational change in MHC-I-β2M complex could alter its interactions with unknown synaptic proteins in AD. To identify proteins that interact with neuronal MHC-I, synaptic proteins binding to MHC-I-β2M complexes were co-purified with W6/32 antibody from the synaptosomes of normal human brain and analyzed with a proteomics approach. In addition to detecting several proteins in synaptosomes previously shown to interact with MHC-I-β2M complex, including GRP78, calnexin, and β-COP [–], liquid chromatography-tandem mass spectrometry (LC–MS/MS) identified a 150 kDa protein that interacted with the stable form of MHC-I (Fig. 3A, Additional file 2: Fig. S2A–C, Additional file 3: Table S2). This protein was subsequently identified as NCAM1, a transmembrane glycoprotein that regulates neurite outgrowth, synaptogenesis, and synaptic plasticity [–]. This NCAM1-MHC-I interaction was confirmed by immunoblotting of the same synapse fraction with antibody to NCAM1 (Fig. 3B) and by its coimmunoprecipitation from SH-SY5Y cells expressing HA-tagged NCAM1 (Fig. 3C, D). The NCAM1–MHC-I interaction was further confirmed by a bio-layer interferometry assay using recombinant NCAM1 and MHC-I-β2M complex, with binding affinity of KD of 31.3 nM (Fig. 3E). Therefore, NCAM1 was identified as a novel interactor of MHC-I in human brain synaptosome.

Inhibition of NCAM1 expression and formation of NCAM1–MHC-I complexes in AD

In summary, we report a novel pathological mechanism of AD, the Aβ-mediated destabilization of the MHC-I-β2M complex and subsequent disruption of NCAM1 signaling. Furthermore, the SCT-mediated restoration of the MHC-I–β2M complex may be a promising therapeutic strategy for restoring synaptic function in AD patients.

Supplementary Information

Although several meta-analyses of genetic risk factors for Alzheimer’s disease (AD) have suggested that MHC-I alleles, specifically HLA-A2.1 and HLA-B7, are associated with AD pathology, the relationship between MHC-I with AD remains unclear because of contradictory reports in differential populations. Amyloid-β (Aβ) peptide is a major pathological factor in synaptic dysfunction. Specifically, oligomeric Aβ dysregulates activity of several synaptic receptors. α-amino-3-hydroxy-5-methyl-4-isoxazolepropionic acid (AMPA) and n-methyl-d-aspartate (NMDA) receptors, whose function and trafficking are regulated by synaptic MHC-I, are, in turn, negatively regulated by Aβ peptide in AD. Additionally, PirB which is a MHC-I receptor expressed in synapses of hippocampal neurons, and is involved in synaptic plasticity during CNS development [–], was identified as an amyloid-β (Aβ) receptor and has been implicated in AD pathology mediated by dysregulated synaptic plasticity with cofilin activation. These findings suggest that MHC-I may have a putative role in AD pathophysiology.

We here addressed this point and revealed that Aβ destabilizes MHC-I complex resulting in decrease of NCAM-1 signaling but restoring MHC-I complex reverses its signaling in Aβ-treated neuronal cells.

Materials and methods

Human brain tissue

Medial temporal gyri from eight patients with AD and seven age- and sex-matched controls were provided by the Netherlands Brain Bank (Additional file 3: Table S1). AD pathological staging was based on the Braak staging system. The hippocampus and cortex from the brains of normal controls and AD patients were analyzed by qRT-PCR, western blotting, synaptosome purification, and immunoprecipitation.

DNA constructs

Because the function of MHC-I is mainly dependent on the protein with which it interacts, the identification of these proteins interacting with neuronal MHC-I is important for understanding MHC-I function in the CNS. We found here that NCAM1 protein is a novel functional receptor of MHC-I in the CNS (Fig. 3). NCAM1 is expressed in the adult CNS, is highly conserved in vertebrates, and is important for neurite outgrowth and synaptic plasticity in the hippocampus. Aβ decreased the interaction of NCAM1 with MHC-I, and NCAM1 downstream signaling (Fig. 4). Further investigation on the mechanism of NCAM decrease induced by Aβ oligomers is required to elucidate role of MHC-I in NCAM stability. While independent effect of Aβ oligomer on NCAM decrease is also possible, SCT-mediated MHC-I stabilization rescue of decreased NCAM levels and restoring synaptic levels suggest MHC-I-NCAM1 interaction role in protecting NCAM1 decrease by Aβ oligomer (Fig. 5). NCAM, being a neuronal marker, is associated in AD. NCAM-deficient mice display reduced exploratory behavior and spatial learning, similar to the symptoms of AD in humans. NCAM levels are lower in frontal and temporal cortex AD patients than control patients and areare increased in serum of AD patients. Aβ mediates the shedding of NCAM2, another neural cell adhesion molecule, leading to loss of glutamatergic synapses. These results uggest that the overall stability of MHC-I is critical for its interaction with NCAM1 and potential role of MHC-I-NCAM1 interaction on pathogenesis of AD.

Various forms and alleles of MHC-I may regulate various synaptic functions via interactions with yet undetermined MHC-I receptors that can distinguish among MHC-I structures, suggesting the difference in regional or individual susceptibility of neurodegeneration in AD. The mechanisms regulating the transition of MHC-I structure and the identification of unidentified MHC-I interaction partners should be investigated further to understand the detailed functions of neuronal MHC-I.

Conclusion
```

</details>

## 4. `1799e7ec`

**Question.** In the Alzheimer's subtype resembling the hippocampal-sparing variant, when does the hippocampus become abnormal relative to the other deep grey matter structures, and where is the loss concentrated?

**Reference answer.** The hippocampus starts becoming abnormal after most of the other deep gray matter structures, with loss predominantly focused in the insula, caudate nucleus and parietal cortex.

**Answer under review.**

> In the Alzheimer's subtype resembling the hippocampal-sparing variant, the hippocampus becomes fully abnormal (Z-score = 3) before atrophy starts in other deep grey matter structures such as the caudate, putamen, insula, precuneus, and middle-temporal cortex. The loss is concentrated primarily in the hippocampus.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
On the other hand, early pathologic damage might explain the decreased FC in AD between the right middle temporal gyrus and the right superior occipital gyrus.

An increased FC has also been associated with mal(adaptive) rewiring of the brain after pathologic damage occurs. This idea is not mutually exclusive to the neurotransmitter dysregulation hypothesis, and the two mechanisms might co-occur in an additive fashion. Some authors have distinguished two types of hyperconnectivity rewiring after brain damage: local hyperconnectivity and global hyperconnectivity. The former states that local alternative paths close to damaged brain areas are used to ensure that communication between networks is possible to preserve function. The latter refers to the brain using multimodal or rich nodes, independently of the localization of the brain damage, in order to ensure the maintenance of cognitive function. Following the popular stages of AD degradation as proposed by research, the first areas damaged in AD (stages I and II) due to TAU deposition are the posterior ones, more specifically, the brain stem followed by the entorhinal. These areas are then followed by the limbic and whole neocortex in more advanced stages (III–IV), and then the hippocampus and anterodorsal thalamic nucleus. As the participants of our study present mild AD, this sign of increased FC in some posterior areas might indicate that certain regions of the posterior cortex could be affected but other areas are still preserved and can be recruited. A study showed increased correlations between occipital regions. Some investigators presented the same results regarding hyperactivity in AD in the middle occipital gyrus, lingual gyrus, and visual cortex and explained the findings as an adaptation of the brain networks in response to the disease.

Although several researchers have justified an increased FC in neurodegenerative diseases as an adaptive mechanism of neuroplasticity to protect behavior and cognition against brain damage, the mechanisms behind FC and its relationship with cognition and behavior are not well understood yet. Multiple factors play a role in FC, and at the time of writing, there is a lack of understanding of what is really causing a specific pattern of FC, i.e., what factors can explain an increased or decreased FC. Currently, interpretations of results in FC have been speculative. For instance, can an increase in FC in several areas be explained simply by structural disconnection

version 3.5.1).

Chi-square and ANOVA tests (α = 0.05) were performed in python (version 3.6.9) to test differences between the diagnostic groups and subtypes.

Results

The disease model identified by SuStaIn consisted of three disease subtypes (Figure 1). The first disease subtype (“Subtype 1” in the next sections), is characterized by abnormality (Z-score = 1) that can be observed in the ventricles first, then atrophy occurs in the hippocampus and entorhinal cortex, that are also the first regions to show full abnormality (Z-score = 3) alongside amygdala. Interestingly, ventricles are also the last regions to show full abnormality meaning a relatively slow but persistent volumetric expansion process that tracks the disease progression.

The second disease subtype (“Subtype 2” in the next sections) shows an atrophy pattern where abnormality starts in thalamus and pallidum (Z-score = 1). Subsequently, atrophy can be observed in caudate, putamen, insula, precuneus and then fusiform gyrus and middle-temporal cortex and hippocampus which is the first biomarker to become fully abnormal (Z-score = 3). In this subtype, ventricles start expanding later than in Subtype 1. The third subtype (“Subtype 3” in the next sections) shows an atrophy pattern where ventricles become fully abnormal before atrophy starts in almost all the other regions, for which a less-defined atrophic progression is manifested in comparison to Subtypes 1 and 2.

SuStaIn subtypes were cross linked to AVRA ratings to evaluate whether similarities between subtypes defined by the two methods exist (Figure 2). Subtype 1 was mainly characterized by the “Typical AD” atrophy pattern; Subtype 2 showed an equal predominance of the hippocampal-sparing variant; Subtype 3 showed a limbic-predominant subtype. The minimal atrophy subtype was most consistent with Subtypes 1 and 2. After correcting against effects of sex, age and TIV, relevant differences (p-value for ANOVA <0.05) in volume of hippocampus were observed between subjects from Subtypes 1 and 2 labeled with minimal atrophy according

Age increases the risk for mild cognitive impairment (MCI), or early dementia, which may impact memory and/or non-memory cognitive domains but typically spares functional abilities. MCI is linked to genetic vulnerability (APOE4), lifestyle and associated comorbidities (e.g., cardiovascular disease, traumatic brain injury, socioeconomic status (SES), education, obesity, depressive symptoms, etc.). Early Alzheimer’s disease accounts for approximately 50% of MCI incidence and is characterized by cognitive decline in memory domains (amnestic type); whereas, vascular dementia, the second most common subtype of dementia with an incidence of 14.5%, is characterized by deficits in non-memory cognitive domains (e.g. visuospatial skills, attention, language, etc.) without memory impairment (nonamnestic type,). A nongradual progression of cognitive deficits is consistent with neurodegenerative disease.

Biomarkers in early Alzheimer’s disease

In 2018, the National Institute on Aging and Alzheimer’s Association Research Framework, updated the definition and diagnostic process to identify Alzheimer’s disease (AD) using pathology markers documented in vivo or at postmortem examination. The advancement in biomarker diagnostic decision making moves away from a syndromal approach (i.e., symptoms and behavioral deficits) to a biological approach for staging AD and other neurological diseases. The understanding of beta amyloid (Aβ) and tau peptides as biomarkers in the CSF (Aβ42, Aβ40, t-tau, p-tau) in AD development has led to the AT(N) scoring system for neuroimaging assessment of AD and other neurological disease: A indicates PET ligand binding of Aβ plaques or low CSFAb42, T, CSF phosphorylated tau, N, neurodegeneration or injury (N). Current progress in detection of AD and other neurological disease depends on the presence of Aβ with or without tau or neurodegeneration in CNS and plasma biomarkers of disease, although p-tau plasma biomarker, NF1 and p-tau217 show promise in longitudinal studies for early AD. The preclinical phase based on biomarker positivity in CSF and PET, occurs prior to the onset of symptoms and is longer than the time of age proposed in MCI-AD. A

) and supported by Alzheimer's Research UK and the Alzheimer's Society, through the Brains for Dementia Research Programme. Funders had no role in the study design, collection, analysis and interpretation of data, writing of the report, or the decision to submit the article for publication.

CONFLICT OF INTEREST STATEMENT

The authors declare no competing interests.

ETHICS STATEMENT

Ethical approval was granted by Brains for Dementia Research City and the East National Research Ethics Service committee.

Supporting information

Data S1.Supporting Information.

Data S2. Supporting information.
```

</details>

## 5. `31598f5f`

**Question.** What sensitivity and specificity did the time-latency classifier achieve for detecting mild cognitive impairment, and at what latency threshold?

**Reference answer.** At a 70 ms time-latency threshold it achieved 88% sensitivity and 87% specificity.

**Note from the gold set.** the source sentence is malformed -- 'The ROC achieved an AUC of 88% sensitivity and 87% specificity'; an AUC is not a sensitivity. The reference answer reads it as intended, and an answer reproducing the paper's own wording must not be penalised.

**Answer under review.**

> The provided context does not contain the answer.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
Introduction

Alzheimer’s disease (AD) is the most common form of dementia and constitutes a significant public health problem worldwide due to the increasing need of social and economic services for patients and their support systems. A particular clinical challenge in AD and related dementias is identifying the early stages of cognitive decline due to its insidious onset and progression. AD is characterized by neuropathological features that can occur 15 to 20 years prior to noticeable changes in cognition or daily function. Mild cognitive impairment (MCI) often represents a transitional stage between normal aging and dementia, and these individuals are at a greater risk of developing incident AD. Detecting early stages of cognitive decline is paramount for identifying those at greatest risk of progression to dementia and who may benefit from further evaluation and treatment. Improving the detection of early cognitive decline may lead to earlier initiation of disease modifying treatments to preserve independent functioning, which is crucial to a patient’s quality of life.

There currently exist numerous tools to help detect early clinical or pathological signs of MCI/dementia, including thorough clinical workups, neuropsychological evaluations, neuroimaging, and blood and cerebrospinal fluid biomarkers. While imaging and biomarker-based techniques can detect some neuropathological features associated with AD, some are invasive and not widely accessible for the purpose of early detection, and others are still in development. Formal neuropsychological evaluation is often an intrinsic part of the diagnostic process for detecting subtle changes in cognitive function in many centers. However, access to neuropsychological services may be limited due to various geographic, economic, and/or psychosocial factors, including limited access to healthcare resources, and therefore cannot be utilized effectively on a large scale. For these reasons, cognitive screening instruments are used as brief and cost-effective methods to identify individuals who require further evaluation and can be implemented across both primary care and specialized clinical settings. Primary care providers often serve as the first line of medical care for older adults concerned about their cognitive performance, yet physicians in primary care settings report feeling ill-equipped to recognize or document signs of cognitive decline, contributing to gross under-detection of MCI in primary care settings. Nonetheless, current screening methods are not sufficiently sensitive or reliable in identifying clinical signs in the very early stages of dementia, and more precise screening techniques that can capture subtle changes in cognition are needed to identify individuals who may benefit from further evaluation.

The participants slept alone in the home bed on the mattress device for 2 consecutive nights. The signal acquisition hardware was placed under the bed connected to the mattress pad using a flat wire powered by battery. After night 2, the device was picked up and data transferred electronically to the laboratory. Participants reported bed and wake times and wore the actiwatch for 7 days. Neurocognitive testing was conducted in a home visit for approximately 90 min. The participant received a $100 Visa gift card for participation.

Statistics and data processing

Multivariable, mixed model regression using group as a factor were used for data analysis for actigraphy, neurocognitive and sleep self-report data moderated by custom covariates as described (e.g., age, education, BMI) with IBM-SPSS, V.26. Demographics were analyzed with one-way ANOVA for continuous variables and Kruskal–Wallis h test for categorical variables. Imputation was used in < 5% of the data.

For the SM-RR coupling output measure, a supervised Neural Network approach was used. SM and RR signals were separated in the frequency domain using FFT and band pass frequency filters as described in Instrumentation and Measures. SM-RR coupling time latency was examined in 10 min windows to determine the Probability Density Function (PDF) of the maximum time latencies for each case. Receiver Operating Characteristic (ROC) statistics were applied to determine sensitivity and specificity, AUC (area under the curve) and c statistic with confidence interval. ROC plot illustrates the diagnostic binary classifier system, in this case, MCI vs. NC as its discrimination threshold is varied. Positive predictive values and negative predictive values were calculated to identify MCI status using sensitivity (true positives) and specificity (false positives). Neural Network and the cross-validation method, Leave-One-Out Covariance (LOOCV), was used to train and test the network. Confusion matrices of true positive, true negative, false positive and false negative were calculated based on the verification group that was placed in an incorrect category by the trained network.

Results

Demographics

We evaluated the prediction accuracy of the DNN model in the two-class classification of MMSE (normal, MMSE scores ≥ 24; cognitive impairment, MMSE scores, ≤ 23). We observed a high prediction accuracy with a sensitivity of 75% and specificity of 87%.

Clinical Experience Using the DNN Model

A total of 165 subjects chose the optional DNN-based dementia risk test at the time of their health examination; most subjects had a normal working life and attended the clinic as a regular health check imposed by the employer on the worker. Figure 6 shows the distribution of the classification of cognitive function based on the MMSE predicted by the DNN model. A total of 94 subjects were classified as Class A (normal), while 67 subjects were classified as Class B (suspected MCI). Only four cases were classified as Class C (suspected dementia).

Thirty out of the 165 subjects (mean age, 56.3 ± 9.4 years) were readmitted to the dementia prevention outpatient clinic at the clinic and underwent a detailed examination of cognitive dysfunction involving various neuropsychological tests, including the MMSE, and imaging-based diagnosis using MRI. Most readmitted patients were classified as class B (suspected MCI) or lower. The predicted MMSE scores (26.2 ± 1.1) were significantly lower than the ground truth MMSE scores (28.2 ± 1.8, p < 0 0.05) (Figure 7).

However, in four cases, the predicted MMSE scores (26.9 ± 1.1) exceeded the ground truth MMSE scores (25.3 ± 0.5); the average difference in the MMSE score was −1.7 ± 0.8. Two of the subjects had a neurological disease, such as subarachnoid hemorrhage (SAH). One patient (male, 66 years old) had SAH due to cerebral aneurysm rupture 2 years before the DNN-based dementia risk test; MRA showed an aneurysm of the anterior communicating artery. The patient had undergone endovascular coiling. At the time of examination, there was no motor paralysis, but mild cognitive decline was observed (MMSE score = 25). The blood test data were within the normal range, and the predicted MMSE score was 27.5.

Relationship Between Blood Data and MRI

Demographic and clinical data of the 174 participants are described in Table 1. The cohort had a mean age of 74.03 years (SD = 8.55), completed an average of 12.45 years of education (SD = 4.72), and included slightly more females than males (56%). Demographic characteristics were similar across groups in the training set, but age and sex were significantly different between clinical groups in the testing sample. MMSE scores were different across groups in both samples (Supplementary Figure S2). A one-way ANCOVA, controlling for age, sex, and years of education, demonstrated a significant difference in mean logit and algorithm scores for every independent model’s prediction across CN, MCI, and all-cause dementia groups, except for phonemic verbal fluency (see Table 4).

[TABLE: Table 4]

Model performance

The final algorithm in the testing sample with the presented tool resulted in an AUC of 0.93 with an overall accuracy of 88.4%, sensitivity of 87.5%, specificity of 89.2%, and F-score of 0.87 in discriminating CN and impaired groups. The final algorithm in the testing sample obtained an AUC of 0.90 with an overall accuracy of 87.5%, sensitivity of 83.3%, specificity of 89.2%, and F-score of 0.80 in discriminating CN and MCI groups. Using Youden’s Index, the optimal threshold value was determined to be 0.45 for impaired (J = 0.767) and MCI (J = 0.725) groups. Figures 3, 4 present accuracy, F-score, sensitivity and specificity for each threshold value when discriminating CN versus impaired and MCI groups in the whole testing set. Since the selected optimal ensemble ML model is RandomForest, the distribution of scores was non-normal and scores fell close to 0 or 1. Therefore, metrics remained constant between the thresholds of 0.23 and 0.70. The mean squared error obtained in the testing set was 0.10 when distinguishing impaired from non-impaired and 0.114 when distinguishing MCI from non-impaired.
```

</details>

## 6. `ef8118ae`

**Question.** What sensitivity and specificity did the time-latency classifier achieve for detecting mild cognitive impairment, and at what latency threshold?

**Reference answer.** At a 70 ms time-latency threshold it achieved 88% sensitivity and 87% specificity.

**Note from the gold set.** the source sentence is malformed -- 'The ROC achieved an AUC of 88% sensitivity and 87% specificity'; an AUC is not a sensitivity. The reference answer reads it as intended, and an answer reproducing the paper's own wording must not be penalised.

**Answer under review.**

> The time-latency classifier achieved a sensitivity of 87.5% and a specificity of 89.2% for detecting mild cognitive impairment at a 70 ms latency threshold.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
group and participants with the lowest scores on the memory tests from the MCI-CON group (n = 3) to comprise the MCI/AI group (n = 20) and a randomly selected subset from the NC group termed NC/AI (n = 20). Using time series correlational analyses, the time latency estimates derived from 10 min segmentation windows across the 2 nights were examined. As described, FFT and digital filters identified two data streams at cutoff frequencies of 0.15 Hz (SM) and 0.37 Hz (RR). Time latency calculations were determined based on identifying events with respiratory frequency change based on a 1 S.D. threshold. Typically, our observations have found that SM precedes RR change (SM → RR). However, for some coupling events, RR preceded SM (RR → SM) and were calculated in the time window. Hence, time latencies may be positive or negative based on whether SM occurred before ( +) or after RR change (-).

The time latency algorithm was tested in the AI analysis as a classifier of MCI risk. Using the cross validation LOOC statistic, the training data set was developed and tested with several validation methods (e.g., Neural Networks, Gaussian and Kernel methods) described in Khosroazad et al.. Figure 3a shows the distribution of time latency using the Neural Network approach where zero is the threshold, 70 ms. Note that the clusters of data points separate MCI from NC cases. We note that the time latency values associated with increased MCI risk were negative, i.e. showed the atypical pattern in which RR change leads SM events. For the ROC diagnostics shown in Fig. 3b., the 70 ms time latency threshold optimized detection of true MCI positive cases (sensitivity) vs. false positives (specificity). The ROC achieved an AUC of 88% sensitivity and 87% specificity.

Discussion

Much recent work demonstrates that sleep and circadian rhythm disturbances in aging-related cognitive decline are clinically significant, and are driven by complex neurodegenerative changes, stress-related cardiorespiratory and autonomic dysregulation, brain inflammation and incomplete β amyloid and tau CSF clearance. Of those who report aMCI symptomatology (i.e., memory loss, cognitive fog, etc.) to their healthcare provider, those who progress to AD are conservative

MCI + dementia) or MCI groups, and areas under the curves (AUC) were used as measures of overall classification accuracy. Accuracy, sensitivity, specificity, and F-scores were calculated for various threshold values for impaired and MCI groups. F-scores represent a common machine learning metric used to measure model accuracy by way of balancing precision and recall, with precision representing the proportion of correct “positive” predictions made by the model, or positive predictive value, and recall representing the proportion of actual positive samples correctly identified by the model, or sensitivity. An F-score value ranges from 0 to 1, with a 1 indicating perfect precision and recall. ANCOVA was used to examine differences in mean logit and algorithm scores by CN, MCI, and all-cause dementia groups, controlling for age, sex, and education. Before performing this test, logit transformation was applied to better meet the assumptions of the test, since the outcome variable might be the prediction of a non-linear ML model, and residuals might show a non-constant spread. Finally, we computed accuracy, sensitivity, and specificity across different MMSE score thresholds for both impaired and MCI groups to compare the classification accuracy with that of the presented model. Statistical analyses were conducted using the statsmodels and pingouin packages in Python.

Results

Descriptive statistics

Demographic and clinical data of the 174 participants are described in Table 1. The cohort had a mean age of 74.03 years (SD = 8.55), completed an average of 12.45 years of education (SD = 4.72), and included slightly more females than males (56%). Demographic characteristics were similar across groups in the training set, but age and sex were significantly different between clinical groups in the testing sample. MMSE scores were different across groups in both samples (Supplementary Figure S2). A one-way ANCOVA, controlling for age, sex, and years of education, demonstrated a significant difference in mean logit and algorithm scores for every independent model’s prediction across CN, MCI, and all-cause dementia groups, except for phonemic verbal fluency (see Table 4).

[TABLE: Table 4]

Model performance

The final algorithm in the testing sample with the presented tool resulted in an AUC of 0.93 with an overall accuracy of 88.4%, sensitivity of 87.5%, specificity of 89.2%, and F-score of 0.87 in discriminating CN

Age increases the risk for mild cognitive impairment (MCI), or early dementia, which may impact memory and/or non-memory cognitive domains but typically spares functional abilities. MCI is linked to genetic vulnerability (APOE4), lifestyle and associated comorbidities (e.g., cardiovascular disease, traumatic brain injury, socioeconomic status (SES), education, obesity, depressive symptoms, etc.). Early Alzheimer’s disease accounts for approximately 50% of MCI incidence and is characterized by cognitive decline in memory domains (amnestic type); whereas, vascular dementia, the second most common subtype of dementia with an incidence of 14.5%, is characterized by deficits in non-memory cognitive domains (e.g. visuospatial skills, attention, language, etc.) without memory impairment (nonamnestic type,). A nongradual progression of cognitive deficits is consistent with neurodegenerative disease.

Biomarkers in early Alzheimer’s disease

In 2018, the National Institute on Aging and Alzheimer’s Association Research Framework, updated the definition and diagnostic process to identify Alzheimer’s disease (AD) using pathology markers documented in vivo or at postmortem examination. The advancement in biomarker diagnostic decision making moves away from a syndromal approach (i.e., symptoms and behavioral deficits) to a biological approach for staging AD and other neurological diseases. The understanding of beta amyloid (Aβ) and tau peptides as biomarkers in the CSF (Aβ42, Aβ40, t-tau, p-tau) in AD development has led to the AT(N) scoring system for neuroimaging assessment of AD and other neurological disease: A indicates PET ligand binding of Aβ plaques or low CSFAb42, T, CSF phosphorylated tau, N, neurodegeneration or injury (N). Current progress in detection of AD and other neurological disease depends on the presence of Aβ with or without tau or neurodegeneration in CNS and plasma biomarkers of disease, although p-tau plasma biomarker, NF1 and p-tau217 show promise in longitudinal studies for early AD. The preclinical phase based on biomarker positivity in CSF and PET, occurs prior to the onset of symptoms and is longer than the time of age proposed in MCI-AD. A

the ORR did not strictly enforce adherence to the planned retrieval delay intervals, which led some individuals to perform recall assessments after prolonged delays. Given the impact of delay length on task performance, we excluded sessions with significantly extended delay periods (more than 240 minutes) resulting in substantial reduction of test sessions in this study. Thus, future implementations of this task, and remote and unsupervised assessments of long‐term memory in general, should make it easier for participants and patients to integrate remote and repeated tests into their everyday life, while still enforcing minimized delay periods.

CONCLUSION

5

Our results demonstrate that unsupervised and remote digital memory assessments could effectively become a valuable tool in the diagnosis and prognosis of AD, conceivably in combination with plasma biomarkers.

CONFLICT OF INTEREST STATEMENT

O.H. has acquired research support (for the institution) from ADx, AVID Radiopharmaceuticals, Biogen, Eli Lilly, Eisai, Fujirebio, GE Healthcare, Pfizer, and Roche. In the past 2 years, he has received consultancy/speaker fees from AC Immune, Amylyx, Alzpath, BioArctic, Biogen, Cerveau, Eisai, Eli Lilly, Fujirebio, Merck, Novartis, Novo Nordisk, Roche, Sanofi and Siemens. S.P. has acquired research support (for the institution) from ki elements/ADDF and Avid. In the past 2 years, he has received consultancy/speaker fees from Bioarctic, Biogen, Eisai, Lilly, and Roche. E.D. reports personal fees from Biogen, Roche, Lilly, Eisai and UCL Consultancy as well as non‐financial support from Rox Health. D.B. and E.D. are scientific co‐founders of neotiv GmbH and own company shares. The other authors report no competing interests. Author disclosures are available in the supporting information.

CONSENT STATEMENT

All human participants provided informed consent to participate.

Supporting information

ICMJE Disclosure Form

Supporting Information
```

</details>

## 7. `c867f698`

**Question.** What did adapting the Clinical Dementia Rating scale for adults with Down syndrome achieve with respect to the distribution of decline scores?

**Reference answer.** It captured a range of cognitive decline and shifted the distribution of decline scores toward lower or no impairment, by adjusting the original questions for premorbid intellectual and functional ability.

**Answer under review.**

> Adapting the Clinical Dementia Rating scale for adults with Down syndrome adjusted cognitive decline scores for premorbid function, which dramatically shifted the score distribution toward no/low impairment.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
-related changes in such individuals.

The Cambridge Examination for Mental Disorders in the Elderly (CAMDEX) is an informant interview developed for neuropsychiatric diagnosis in the elderly, including dementia. It was modified for use in DS (CAMDEX-DS). The CAMDEX-DS consists of approximately 150 questions that ask about functional difficulties in different cognitive domains, whether such difficulties represent a deterioration in function, and the extent of the deterioration (slight or great). The CAMDEX-DS has moderate to high inter-rater reliability, good predictive validity, and correlates with change in independent cognitive tasks administered to DS adults longitudinally.

The Dementia Screening Questionnaire for Individuals with Intellectual Disabilities (DSQIID) was more recently developed and is gaining wider use and popularity. The DSQIID focuses specifically on change in function relative to a premorbid level; it is brief and easy to complete by a single informant. It has been translated into multiple languages including Chinese and Italian, and along with the original English version, all versions have good psychometric properties.

In addition to these advances, it would be desirable to adapt clinical staging instruments that are widely utilized in scientific and clinical work involving AD dementia in the broader population to afford comparability of assessment and staging for scientific and clinical efforts involving individuals with DS. Therefore, we adapted the Clinical Dementia Rating scale (CDR) for use in DS. The CDR is a semi-structured clinical diagnostic interview that is an integral component of the Uniform Data Set that is used by all federally funded Alzheimer Disease Centers (ADC) to determine the presence or absence of dementia for individuals being evaluated at ADCs. The semi-structured interviews are administered separately to an informant and then to the research participant or patient and focus on capturing intra-individual change from previous cognitive and functional performance levels. An experienced clinician then synthesizes the information from the interview to determine the presence or absence of dementia and, when present, its severity. A CDR score of 0 indicates cognitive normality, whereas scores of 0.5, 1, 2, and 3 indicate very mild, mild, moderate, and severe dementia, respectively.

The primary goal of this project was to determine whether adaptations of the CDR for DS—by both interview and caregiver report—could reliably capture variation among DS patients when implementing new adaptations of an established dementia rating scale.

Methods

Sample

In the first study phase, families with DS adults aged 18 years and older were recruited from the St

Background

Alzheimer disease (AD) is the most common cause of dementia. Because of the aging population worldwide, AD is reaching epidemic proportions; in 2018, an estimated 5.5 million United States citizens age 65 and older had AD, which is projected to grow to 13.8 million by the middle of this century if no effective therapies are developed to prevent, slow, or stop the disease. Down syndrome (DS) is the most commonly identified genetic cause of cognitive impairment. Adults with DS have an increased risk for developing AD dementia owing to the trisomy of chromosome 21 where the amyloid precursor protein (APP) gene is located leading to overexpression of both APP mRNA and amyloid beta (Aβ) peptide. Dementia is often identified earlier in adults with DS compared with the typical aging population, with estimates of about 10% in DS adults in their 40s, about 30% in their 50s, and as high as 80% of DS adults in their 60s [–].

Cognitive and functional decline are the salient indicators of AD. DS adults have pre-existing and varying levels of intellectual disability and cognitive impairment making it difficult to assess change relative to a typical level of functioning. In the DS population, assessment of change in cognitive function must take into account baseline cognitive abilities. One of the first instruments to be modified for use in DS was the Dementia Questionnaire for Persons with Mental Retardation (DMR, since renamed the Dementia Questionnaire for People with Learning Disabilities (DLD)). Criticisms of the DMR/DLD include lack of assessment of change from earlier level of functioning, which results in significant floor effects, and use of different cutoff scores of increasing stringency for higher levels of intellectual disability, the latter of which is not always known or possible to assess [–].

The Dementia Scale for Down Syndrome (DSDS) is an informant interview specifically for use in DS. It contains a total of 60 items scored as present, absent, typical of the individual, or not applicable; 20 items assess early-stage dementia, 20 items assess middle stage dementia, 15 items assess late-stage dementia, and 5 items assess very late-stage dementia. The DSDS was developed and standardized in a sample of adults the majority of whom had severe to profound intellectual disability; hence, the most common criticism is that it may not be sensitive enough to detect dementia in higher functioning individuals. A counterargument to this criticism is that informants may not be able to detect early dementia

were difficult because DS participants in our study were never alone and informants could not evaluate whether the DS adult would be able to find his/her way around familiar streets, for example. Ability to manage a household emergency like a small leak or fire did not seem applicable in our sample, again, since DS adults were almost never alone—even those who live independently have scheduled visitors and structured days. Ability to drive a vehicle or do calculations was absent in our entire sample.

Based on our data and on personal interaction with DS adults and their family members, ongoing research should continue to focus on elements of caregiver report and direct assessment of the DS individual that will optimize differential diagnosis. The primary goal of this study was to adapt the widely used CDR for assessment of dementia in adults with DS. We have shown that such adaptation was successful in capturing a range of cognitive decline and in shifting the distribution of decline scores toward lower/no impairment by adjusting original CDR questions to take into account premorbid intellectual and functional ability. Future work of the CDR-QDS and CDR-IDS should include comparison with existing instruments such as the CAMDEX-DS and DSQIID, with neuropsychological performance, and with other biomarkers, such as positron emission tomography for amyloid or tau.

Conclusions

The modified CDR questionnaire (CDR-QDS) and interview (CDR-IDS) instruments capture a range of impairment in DS adults. Adjustment of cognitive decline scores for premorbid function dramatically shifted the score distribution toward no/low impairment and was an important element in identifying DS adults with suspicion for dementia. The DSDS indicated high suspicion of dementia in two of twenty-two individuals in this sample who had broadly elevated scores on the modified CDR instruments. The modified CDR instruments captured a range of subthreshold impairments in cognitive function that may prove extremely useful in prospective studies of the development of AD in DS. Moreover, future research is warranted to use quantitative scales such as these to help differentiate dementia from other neuropsychiatric problems in DS, including catatonia, adjustment disorder, and a range of psychiatric comorbidities, all of which are potentially treatable and for which inappropriate/premature assignment of a diagnosis of dementia may be extremely misleading and result in a major obstacle to appropriate care and treatment. For DS adults with elevated scores for cognitive impairment in this study, the impairment generally encompassed multiple cognitive domains and was not predominantly within the memory
```

</details>

## 8. `e93def72`

**Question.** How did a higher-risk ApoE genetic profile relate to blood-brain barrier biomarkers and to the amyloid 42/40 ratio?

**Reference answer.** It did not affect blood-brain barrier biomarkers, but was associated with lower amyloid 42/40 ratio levels in a dose-dependent manner (H (4) = 9.973, p = 0.041).

**Answer under review.**

> A higher-risk ApoE genetic profile did not affect blood-brain barrier (BBB) biomarkers but was associated with lower levels of the Aβ42/40 ratio in a dose-dependent manner. Specifically, the Kruskal–Wallis group comparison among different ApoE groups divided by graded risk factor showed this association with a p-value of 0.041.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
Statistical analysis: Statistical analysis was conducted with MATLAB (ver R2019a) and JASP (JASP team, 2019). According to the normality of the data, between-group differences within the ATN framework were analysed using either a frequentist one-way analysis of variance (ANOVA) or Kruskal–Wallis H test, followed by Bonferroni post-hoc correction. Based on ApoE genotype, a value was assigned according to the graded risk factor associated to each genotype, with consecutive values given to E2/E2, E2/E3, E3/E3, E2/E4, E3/E4, and E4/E4 according to Reiman et al.. Sex correlations are calculated as male/female ratio, with negative values implying an increased male/female ratio. Correlations between continuous variables were investigated using linear regression. Principal component analysis (PCA) using an oblique promax rotation was used to reduce data dimensionality among multiple variables. Statistical significance was set at p-value < 0.05.

5. Conclusions

Our data showed that BBB dysfunction does not change across different ATN subtypes and that is not correlated with cognitive impairment. However, BBB damage, if measured by Qalb, is associated with low Aβ40 levels, which might potentially have implications for the fine-grain balance between different amyloid species. BBB disruption was not modulated by ApoE status, which, however, showed a dose-dependent effect on the Aβ42/40 ratio. Further studies are needed to replicate these findings including a cohort of cognitively unimpaired individuals and to investigate how blood-based AD-specific biomarkers are impacted by a disruption of the BBB. We hope that this data will highlight the need for further research in this field, which might be crucial for diagnostic and therapeutic purposes.

While many different CSF biomarker ratios have been evaluated to increase diagnostic accuracy, since the introduction of the amyloid (A), tau (T), and neurodegeneration (N) ‘ATN’ system, each single biomarker is regarded as reflecting a separate construct, the combination of which will determine diagnostic labelling. In the context of CSF biomarkers, phosphorylated tau (p-tau) reflects the tau (T) status of an individual, the total presence (t-tau) of neurodegeneration (N), and either amyloid β42 (Aβ42) or the Aβ42/40 ratio of the pathological amyloid deposition (A) in the brain. The Aβ42/40 ratio outperforms Aβ42 alone in increasing diagnostic accuracy, given the wide range of interindividual variability in the rate of production and drainage of amyloid. There is no consensus whether Aβ40 levels remain substantially unaffected in the various forms of dementia, or even show higher values in patients with AD, and mild cognitive impairment (MCI). However, the selective decrease in Aβ42 compared to constant or even elevated Aβ40 seems to be specific for AD, with a cut-off of 0.6 for the Aβ42/40 ratio showing good diagnostic accuracy, and a stronger correlation than Aβ42 alone to amyloid positron emission tomography (PET) and AD neuropathology.

Although Aβ is found in the blood at the same concentration of CSF (0.1–0.5 nM), Aβ deposits are largely found in the interstitial compartments within the brain. The relationship between serum and CSF levels of Aβ and tau peptides has been the target of the recent diagnostic efforts to develop blood-based biomarkers, which are now being extensively validated and increasingly incorporated into the design of clinical trial. In this era of intensive shift to blood-based assays, it is crucial to investigate the fine-grain balance between the serum and CSF concentration of AD-specific biomarkers, such as t-tau, p-tau, Aβ42, Aβ40, and the Aβ42/40 ratio, but also to understand if their relationship with other molecules such as albumin may indirectly play a role.

BBB biomarkers were not impacted by the ApoE genotype, but our data support a modulation of the Aβ42/40 ratio with ApoE status. This seems to follow a dose-dependent effect, with ApoE phenotypes at higher risk of developing AD being associated with a lower Aβ42/40 ratio. This result is in line with the previous literature on the association between carrying at least one ApoE4 allele and lower levels of amyloid but not higher levels of tau in the CSF, but extends these findings to participants with different ATN statuses. Moreover, it shows a dose-dependent effect across different genetic subtypes including participants with at least one ApoE2 allele. We were also able to show that ApoE status was not associated with BBB disruption in this sample, which is in line with previous negative findings in ApoE4 positive individuals.

Qalb was correlated with Aβ40 levels (r = −0.190, p = 0.014), but not with Aβ42 or the Aβ42/40 ratio. Patients were then divided according to the integrity of their BBB using the standard age-related Qalb cut-off of eight as having normal Qalb (<8) or high Qalb (>8). We found that the negative correlation between Aβ40 and Qalb was only significant (r = −0.367, p = 0.009) in patients with high Qalb, while in patients with normal Qalb this was not observed (Figure 1). No other significant correlations were found.

2.3. Relationship between BBB Biomarkers, Demographics, and Cognition

MMSE scores were not correlated with the BBB markers studied but were positively correlated with Aβ42 levels, with lower MMSE associated with lower levels of Aβ42 (r = 0.227, p = 0.011). Age was negatively correlated with serum albumin (r = −0.240, p = 0.001), with lower levels of serum albumin seen in elderly individuals. Females had lower CSF proteins (W = 5084, p < 0.001), CSF albumin (W = 4825, p < 0.001), CSF IgG (W = 4951, p < 0.001), and Qalb (W = 4942, p < 0.001). A correlation matrix across all variables in shown in Figure 2.

The Kruskal–Wallis group comparison among different ApoE groups divided by graded risk factor showed that carrying a more high-risk genetic profile did not affect BBB biomarkers but was associated with lower levels of Aβ42/40 ratio in a dose-dependent manner (H (4) = 9.973, p = 0.041), as seen in Figure 3. As there was only one subject with E2/E2 genotype, that subject was excluded from statistical analysis but kept for data visualization purposes.

2.4. Principal Component Analysis

Background

The ε4 allele of the apolipoprotein E gene (APOE-ε4) is the strongest genetic factor for late-onset Alzheimer’s disease. Compared with those individuals with an APOE ε3/ε3 genotype, white individuals with one copy of the ε4 allele show an increased lifetime risk of developing Alzheimer's disease (AD) (ε2/ε4, OR 2.6; ε3/ε4, OR 3.2). The risk is much higher for carriers of two copies (ε4/ε4, OR 14.9). The main roles of the ApoE protein, encoded by the APOE gene, include lipid transport and clearance of amyloid deposition. However, the ε4 isoform of the ApoE protein shows an impaired capacity to perform these functions compared with the other isoforms. Such impaired function may underlie the observed effects of APOE-ε4 on the brain throughout the lifespan. In particular, APOE-ε4 has been related to earlier and increased amyloid-β deposition, one of the neuropathological hallmarks of AD. However, the effects on brain morphology have been reported to be subtler. Most of the studies so far have stratified individuals in only two levels of risk (APOE-ε4 carriers vs noncarriers). However, APOE-ε4 homozygotes, who completely lack expression of the most efficient isoform of the ApoE protein, are an interesting population to study to gain a better understanding of the mechanisms through which APOE genotype modulates the risk of AD. Given the essential implication of ApoE in the transport of cholesterol, the main component of the myelin sheath, it is conceivable that alterations in white matter (WM) microstructure may be one of these mechanisms.
```

</details>

## 9. `f431daa4`

**Question.** What CSF tau threshold defined tau positivity in the linear mixed-effects models of vascular biomarkers?

**Reference answer.** Tau positivity was defined as a value above 24.8 pg/mL.

**Answer under review.**

> The provided context does not contain the answer.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
, and education-adjusted linear mixed models (LMMs) with subject-specific intercepts. For all LMMs, a random slope was added when it improved model fit by comparing the Akaike information criterion using χ2 statistics. Tau marker (tau PET or plasma pTau181), time (tau PET or blood collection as T = 0), and an interaction term of tau marker × time were entered as fixed variables and neuropsychological test performance as a dependent variable. For all LMMs, we used separate models per tau marker and per cognitive test. Furthermore, tau markers and cognitive scores were scaled within each LMM to compare effect sizes. The fixed effect of tau marker was interpreted as the cross-sectional association, and the fixed effect of tau marker × time was interpreted as the longitudinal association. P values were corrected for multiple testing by applying the 10% false-discovery rate (FDR).

Lastly, in the subset with longitudinal tau markers, we investigated changes in tau markers over time using age- and sex-adjusted LMMs. Time, diagnosis (SCD or MCI/AD), and an interaction term of diagnosis × time were entered as fixed variables and tau marker as a dependent variable. We additionally explored associations of tau marker annual changes with cognitive decline, for which tau marker annual changes were calculated as [(follow-up − baseline)/time between measurements in years]. Age-, sex-, and education-adjusted LMMs were performed with tau marker annual change, time (baseline tau PET or blood collection as T = 0), and an interaction term of tau marker annual change × time as a fixed variable and neuropsychologic test performance as a dependent variable. The fixed effect of tau marker annual change × time was interpreted as the association between tau marker annual change and longitudinal cognition.

RESULTS

Participants

Table 1 shows the participant characteristics. Mean age was 65.4 ± 7.4 y, and 48.2% of participants were female. By study design, all MCI/AD participants were Aβ-positive. Of the 50 SCD participants, 19 (38.0%) were Aβ-positive. There were no group differences in age, sex, or education, but there were more APOE ɛ4 carriers in MCI/AD than in SCD (P < 0.01). Supplemental Table 1 shows the characteristics of the longitudinal subset. Plasma pTau181 did not correlate with age or sex in either

.52 was chosen as the value at which an individual was equally likely to belong to either component of the bimodal distribution. This cutpoint is highly consistent with a published cutpoint (tau/Aβ42 > 0.54) for AD biomarker positivity using the Lumipulse assays, derived against clinical read of amyloid PET scans and validated in multiple cohorts.

Statistical analysis

Demographics and clinical characteristics between those with and without CSF were compared by Student’s t-test and chi-squared tests as appropriate. Relationships between PWV and performance in each cognitive domain were analyzed with separate linear models adjusted for age, sex, education, and FSRP. These analyses were then repeated with APOE genotype or CSF AD biomarker status (+/-) added to explore the interaction of PWV and AD risk markers (APOE ε4+; tau/Aβ42+) on cognition (while adjusting for age, sex, education, and FSRP).

Additional post hoc analyses were performed to determine whether significant results were retained in models including the individual FSRP components in place of the overall FSRP. That is, in cases where there were significant results, we reran the primary analyses described above but in place of overall FSRP instead adjusted for systolic blood pressure, history of diabetes, cardiovascular disease and/or atrial fibrillation, current smoking, and use of antihypertensive medication. We also reran these analyses with the individual FSRP components listed above while adjusting for two more vascular risk factors: BMI and history of transient ischemic attack (TIA).

Results

Associations of PWV with participant characteristics

Across the cohort, there was a significant increase in PWV with increasing age in both men and women (p < 0.001), with no evidence of an interaction between sex and age (p =.89). Overall, men had higher PWV than women (p < 0.001) (Fig. 1A). There was no significant association between PWV and APOE ε4 status (Fig. 1B), nor between PWV and the level of CSF Tau or Aβ42, or the tau/Aβ42 ratio (Fig. 1C).

Associations of PWV with cognitive test performance

Performance on each of the cognitive domain scores is presented as a function of PWV in Fig. 2A. After adjusting

equations. Diagnostic performance of Lumipulse assays for the CSF markers or their ratios to distinguish between AD patients and controls was assessed by means of a receiver operating characteristic (ROC) curve analysis. Optimal cut-offs were determined by maximizing the Youden index and sensitivity, and specificity was calculated. The ROC curves were compared according to the area under the curve (AUC) comparison method of DeLong et al.. Overall percentage of agreement (OPA) between Lumipulse and INNOTEST results were calculated as the sum of participants classified as “positive” or as “negative” by both modalities over the total number of participants. OPA was calculated both for each individual marker and their ratios as well as for the overall CSF profile. In accordance with the National Institute on Aging and Alzheimer’s Association criteria, subjects were classified as having a CSF-AD profile when they showed a positive β-amyloid plaques marker (either reduced Aβ42 or reduced Aβ42/Aβ40 ratio) in combination with a positive marker of fibrillary tau (increased p-Tau concentration).

Results

Analytical performance of Lumipulse assays

Results for intra-assay and inter-assay coefficients of variation (CVs) for the four Lumipulse assays are shown in Table 1. Intra-assay CVs for low, medium, and high concentration CSF samples ranged from 1.9 to 2.8% for Aβ42, from 0.8 to 1.4% for Aβ40, from 0.9 to 3.5% for t-Tau, and from 0.7 to 1.1% for p-Tau. CVs for inter-assay variation were 2.1–3.3% for Aβ42, 3.6–5.5% for Aβ40, 0.8–4.8% for t-Tau, and 2.0–3.6% for p-Tau. [TABLE: Table 1]

Method comparison between INNOTEST and Lumipulse assays

Baseline characteristics at the time of lumbar puncture of neurological controls and AD patients are presented in Table 2. The population age ranged from 42 to 82 years old in controls and from 49 to 88 years old in AD patients, the latter being slightly but significantly older (p = 0.013). The female-to-male ratio was similar in both groups, and
```

</details>

## 10. `ae0e2ca6`

**Question.** Which novel MHC-I partner does amyloid-beta-oligomer destabilisation of the synaptic MHC-I-beta2M complex impair the interaction with, and what reversed the resulting signalling impairment?

**Reference answer.** NCAM-1; inhibiting the amyloid-beta-induced destabilisation of the MHC-I complex with SCT reversed the neuronal signalling impairment.

**Answer under review.**

> The amyloid-beta-oligomer destabilization of the synaptic MHC-I-beta2M complex impairs the interaction with NCAM-1. This impairment was reversed by stabilizing the MHC-I-β2M complex.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
Discussion

The present study revealed that Aβ oligomers destabilizes synaptic MHC-I-β2M complex, impairing the interaction with NCAM-1, a novel MHC-I partner. We here further showed that inhibiting the Aβ-induced destabilization of MHC-I complex by SCT can reverse the neuronal signaling impairment, harnessing a novel therapeutic strategy.

Although studies have been made about the role of neuronal MHC-I in synaptic plasticity, little was known about MHC-I function in neurological diseases. Especially, the connection between MHC-I function and its role in AD remained unclear, despite genetic analyses showing an increased frequency of some MHC-I alleles in individuals with AD. We here found that the unstable β2M-free MHC-I heavy chain was increased in AD brains (Fig. 2). The oligomeric Aβ was largely responsible for the destabilization of neuronal MHC-I-β2M complexes (Fig. 1). Aβ treatment caused MHC-I-β2M complex to degenerate into soluble β2M and β2M-free MHC-I heavy chain, leading to rapid internalization of MHC-I heavy chain followed by lysosomal degradation (Fig. 1). This β2M-free MHC-I heavy chain was also found to regulate synapse density negatively in glutamatergic neurons, which may be related with synapse loss in AD brains. MHC-I was also recently reported to be involved in the pathogenic mechanisms of the strongest risk factor of sporadic AD, apolipoprotein-E4.

Since NCAM1 is a novel interacting partner of neuronal MHC-I-β2M complex (Fig. 3) and MHC-I-β2M is destabilized by Aβ oligomers and in AD brains (Figs. 1, 2), we speculated that the interaction of NCAM1 with MHC-I-β2M complex is also deregulated. As expected, co-immunoprecipitation assay showed reduction in the amount of NCAM1-MHC-I-β2M complex in AD brains (Fig. 4A, B). In primary neurons, NCAM1 co-localized with MHC-I at the surface of the soma or dendrites, however Aβ oligomer reduced the co-localization intensity between MHC-I and NCAM1 or each protein levels (Fig. 4C–E). Aβ treatment reduced the amount of NCAM1 interacting with MHC-I by about 50% relative to control in primary neurons (Fig. 4F, G). Aβ treatment also reduced CREB phosphorylation, which is part of the final cascade of NCAM1 signaling (Fig. 4H, I), suggesting that the MHC-I–β2M complex is important for interacting with NCAM1 and activating its signaling. Together, these observations suggested that Aβ-mediated destabilization of MHC-I-β2M complex eventually impairs the formation of NCAM1-MHC-I-β2M complex, subsequently dysregulating NCAM1 signaling.

Stabilization of MHC-I-β2M complex rescued Aβ-mediated MHC-I depletion and dysregulation of NCAM1-MHC-I interactions

Although several meta-analyses of genetic risk factors for Alzheimer’s disease (AD) have suggested that MHC-I alleles, specifically HLA-A2.1 and HLA-B7, are associated with AD pathology, the relationship between MHC-I with AD remains unclear because of contradictory reports in differential populations. Amyloid-β (Aβ) peptide is a major pathological factor in synaptic dysfunction. Specifically, oligomeric Aβ dysregulates activity of several synaptic receptors. α-amino-3-hydroxy-5-methyl-4-isoxazolepropionic acid (AMPA) and n-methyl-d-aspartate (NMDA) receptors, whose function and trafficking are regulated by synaptic MHC-I, are, in turn, negatively regulated by Aβ peptide in AD. Additionally, PirB which is a MHC-I receptor expressed in synapses of hippocampal neurons, and is involved in synaptic plasticity during CNS development [–], was identified as an amyloid-β (Aβ) receptor and has been implicated in AD pathology mediated by dysregulated synaptic plasticity with cofilin activation. These findings suggest that MHC-I may have a putative role in AD pathophysiology.

We here addressed this point and revealed that Aβ destabilizes MHC-I complex resulting in decrease of NCAM-1 signaling but restoring MHC-I complex reverses its signaling in Aβ-treated neuronal cells.

Materials and methods

Human brain tissue

Medial temporal gyri from eight patients with AD and seven age- and sex-matched controls were provided by the Netherlands Brain Bank (Additional file 3: Table S1). AD pathological staging was based on the Braak staging system. The hippocampus and cortex from the brains of normal controls and AD patients were analyzed by qRT-PCR, western blotting, synaptosome purification, and immunoprecipitation.

DNA constructs

Destabilization of MHC-I-β2M complex in AD brains

To investigate whether impaired MHC-I-β2M complex was involved in AD pathology, we investigated synaptic MHC-I levels in AD brains because functional neuronal MHC-I is mainly localized to the synapses. Among the hippocampal fractions in normal brains, almost 60% of total MHC-I was in the synaptic fractions (Fig. 2A, B), a finding confirmed by assessing the expression of several synaptic proteins, including synaptophysin, VGAT, and postsynaptic density (PSD)-95. NeuN, a neuronal nuclear protein, localized to the non-synaptic fractions, also confirming the purity of isolated synaptosomes. MHC-I and β2M levels were reduced 50% in synaptic fractions of AD brains (Fig. 2A–C). The synaptic proteins including synaptophysin and PSD95 were also downregulated in AD synapses (Fig. 2A, D), indicating synaptic degeneration in AD brains. Higher PSD95 localization in non-synaptic fraction may reflect the shift in the distribution of PSD95 from post-synapse to other regions as disease progression. Together, these results indicated that synaptic levels of MHC-I and β2M are reduced in AD brains. Using two kinds of MHC-I conformation-specific antibodies, immunoprecipitation analysis demonstrated that most synaptic MHC-I in synaptosomes of control brains was present in W6/32-sensitive MHC-I-β2M complex form (Fig. 2D, E). In AD synaptosomes, however, most synaptic MHC-I was present as HC-sensitive β2M-free MHC-I heavy chains (Fig. 2D, F).

Aβ oligomers induced extracellular release of β2M which was dissociated from surface MHC-I-β2M complex (Fig. 1E, H). Several proteomics analyses have identified β2M as a potential biomarker in the CSF of patients with AD. Interestingly, β2M is a pro-aging factor that impairs cognitive function and neurogenesis, implying relations with AD. β2M could induce cognitive decline via neuroinflammation through toll-like receptor 4 (TLR4). Hence, the increased release of β2M downstream from Aβ-induced dissociation of MHC-I-β2M complex (Fig. 1) could be related with neuroinflammation and neurodegeneration in AD. How Aβ oligomer dissociates MHC-I-β2M complex is yet uncertain. Aβ oligomer might dissociate MHC-I complex directly or indirectly via unknown mechanisms. Leukocyte immunoglobulin like receptor B2 (LilrB2) is a well-known binding partner with MHC-I. Aβ oligomers bind to LilrB2, which might be a way of dissociating MHC-I-β2M complex indirectly. LilrB2 has a binding preference to β2M-free MHC-I heavy chains rather than the MHC-I-β2M complex in vitro. Additional studies are required to assess the detailed mechanism of MHC-I dissociation and toxic effects of Aβ-mediated extracellular β2M.
```

</details>

## 11. `724f8965`

**Question.** Which plasma biomarkers contributed significantly to predicting both PACC and risk of Alzheimer's dementia, and what did plasma NfL appear more useful for?

**Reference answer.** Plasma P-tau217 and Abeta42/Abeta40 contributed significantly to the prediction of both PACC and risk of AD dementia, while plasma NfL added significant prognostic information for PACC and appeared more useful for predicting general cognitive decline and risk of all-cause dementia.

**Answer under review.**

> Plasma P-tau217 and Aβ42/Aβ40 contributed significantly to predicting both PACC and risk of Alzheimer's dementia. Plasma NfL appeared more useful for predicting general cognitive decline (MMSE) and risk of all-cause dementia.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
All three plasma biomarkers were significantly associated with the primary outcomes on their own, but we showed here that they also provide some degree of overlapping information with each other. Plasma P-tau217 and Aβ42/Aβ40 contributed significantly to the prediction of both PACC and risk of AD dementia, while plasma NfL added significant prognostic information for PACC and appeared more useful for predicting general cognitive decline (MMSE) and risk of all-cause dementia. Together, our results demonstrate the wide applicability of this plasma biomarker panel in a CU elderly population.

All three plasma biomarkers also significantly reduced sample sizes needed to run AD clinical trials in a CU population when used for pre-trial inclusion screening. This is a promising result given that clinical trials of AD are increasingly focused on elderly individuals without existing cognitive impairment. Running such a clinical trial in a cost-effective way likely requires the ability to easily and affordably identify CU individuals at risk of developing AD. Our results suggest that these plasma biomarkers are in fact an effective way to enrich clinical trials in a CU population, and that they even add additional value in a population which has already been enriched for SCD status. While the biomarkers showed promise for stand-alone use for trial enrichment, combining them in a multivariable model led to the greatest reduction in required trial sample size and the lowest variability in estimated sample size reduction.

Interestingly, the combined multivariate model and individual plasma biomarkers were robust to variation in the inclusion threshold, indicating that random shifts in the demographics of a clinical trial screening population or in the analytical variability of the plasma assay may not have a significant negative impact on the effectiveness of such an enrichment scheme. Still, this result should be interpreted with caution since it is not easy to determine how much of the variability is controllable (e.g., through pre-analytical factors) and how much is due to inherent biological variability. It was also not possible to account for the possibility that enrichment may increase study attrition rates or otherwise alter trial dynamics since this type of data is not available to us.

We first tested whether plasma biomarkers were significantly associated with cognitive decline as measured by the PACC. When added individually to a basic model consisting of age, sex, and education (Fig. 1), we found that plasma P-tau217 had the strongest association with longitudinal change in PACC (β = −0.20 points per year per SD increase in biomarker value, P < 0.0001), followed by plasma Aβ42/Aβ40 (β = −0.18, P = 0.0002), and plasma NfL (β = −0.16, P = 0.001). When combining all three plasma biomarkers together in the same model (Table 2), all three biomarkers remained significant (P = 0.004 for Aβ42/Aβ40, P = 0.002 for P-tau217, P = 0.01 for NfL). Adding APOE ε4 status to the basic model did not affect the significance of any biomarkers in either the combined or individual models (Supplementary Table 1), although the effect of plasma Aβ42/Aβ40 in the combined model decreased the most (β = −0.16, P = 0.002 with APOE ε4 status).[TABLE: Table 2]

All plasma biomarker models significantly improved prediction of PACC change compared to the basic model (AIC = 6699; R2 = 0.07, CI [0.06, 0.11]; see Table 2). In terms of AIC, a combination of all three plasma biomarkers predicted PACC change best (AICΔ = −28 versus basic model; R2 = 0.14 [0.12, 0.17], P < 0.0001), followed by plasma Aβ42/Aβ40 only (AICΔ = −14; R2 = 0.11 [0.09, 0.14], P < 0.0001), plasma P-tau217 only (AICΔ = −13; R2 = 0.09 [0.08, 0.13], P = 0.0002), and finally plasma NfL only (AICΔ = −9; R2 = 0.10 [0.08, 0.14], P = 0.002).

Because SCD participants had a significantly higher risk of AD dementia (see Table 1), we also tested whether plasma biomarkers would reduce the required sample size of a clinical trial above and beyond what could be achieved if participants were already screened for SCD status (Supplementary Table 9). To start, screening for SCD status by itself did not lead to a significant reduction in sample size with PACC as trial outcome (SSΔ = 19%, CI [−10, 48], P = 0.38), but did lead to a significant reduction in sample size with conversion to AD dementia as trial outcome (SSΔ = 55%, CI [46,62], P < 0.001). For PACC, we found an increased effect of plasma Aβ42/Aβ40 (SSΔ = 51%, CI [17,75], P = 0.007), plasma NfL (SSΔ = 61%, CI [25,82], P = 0.001), and the combined model (SSΔ = 73%, CI [53,87], P < 0.001), but a decreased effect of plasma P-tau217 (SSΔ = 44%, CI [−10, 70], P = 0.09). With AD dementia as outcome, the plasma Aβ42/Aβ40, plasma P-tau217, and combined models remained significant while the plasma NfL model remained non-significant.

Discussion

We tested the hypothesis that plasma biomarkers (Aβ42/Aβ40, P-tau217 and NfL) previously established in AD research improve prediction of both cognitive and clinical outcomes for elderly CU individuals. Our primary findings were that plasma biomarkers add significant prognostic information to a basic model consisting only of demographic information (age, sex and education) and can significantly reduce the number of participants required to run AD-related clinical trials in this population.

We therefore tested the usefulness of plasma Aβ42/Aβ40, P-tau217, and NfL (separately and combined) for predicting longitudinal cognitive decline and clinical outcomes in a CU population comprised of both cognitively normal (CN) healthy controls and individuals with subjective cognitive decline (SCD) who did not meet the diagnostic criteria for MCI. We hypothesized that a combination of ATN plasma biomarkers could improve the prediction of cognitive decline and risk of AD dementia compared to using only basic demographic information. We also investigated the extent to which plasma biomarkers could reduce the sample size required to adequately run AD clinical trials in a CU elderly population.

Results

Study population characteristics

A total of 435 CU individuals were included of which 167 (38.4%) had SCD. During follow-up, a total of 28 individuals converted to AD dementia (6.4%) and 39 individuals converted to all-cause dementia (9.0%). SCD participants had significantly lower baseline Mini-Mental State Examination (MMSE, P < 0.001) and Preclinical Alzheimer’s Cognitive Composite (PACC, P < 0.001) scores, a significantly higher risk of AD dementia (P < 0.001), and significantly higher baseline plasma NfL levels (P = 0.04). However, there was no difference in longitudinal change in MMSE (P = 0.41) or PACC (P = 0.10), nor in baseline plasma Aβ42/Aβ40 (P = 0.72) or P-tau217 (P = 0.28) levels, between CN and SCD participants. Study population characteristics are provided fully in Table 1.[TABLE: Table 1]

Association between plasma biomarkers

When testing the associations between unadjusted plasma biomarker values using Spearman correlation (Supplementary Fig. 1), there was a significant correlation between Aβ42/Aβ40 and P-tau217 (ρ = −0.22, P < 0.0001), between P-tau217 and NfL (ρ = 0.20, P = 0.0005), and between NfL and Aβ42/Aβ40 (ρ = −0.10, P = 0.03).

A total of 201 participants (46.2%) were plasma Aβ42/Aβ40-positive, 162 participants (37.2%) were plasma P-tau217-positive, and 165 participants (37.9%) were plasma NfL-positive.

Modeling longitudinal change in cognition
```

</details>

## 12. `538b9950`

**Question.** What R-squared and p-value were reported for the linear regression between CSF GFAP and 18F-FDG brain uptake in BA9?

**Reference answer.** R2 = 0.1806, with F (1,27) = 5.069 and p = 0.0342.

**Answer under review.**

> The R-squared value for the linear regression between CSF GFAP and 18F-FDG brain uptake in BA9 was 0.1806, and the p-value was 0.0342.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
see Figure 1), with peaks in BA 6, 9 and 11 [see Table 2].

Moreover, a significant negative relationship between brain glucose consumption and CSF levels of β-S100 was also found in a wide cluster that included the left supramarginal gyrus, the inferior parietal lobe and middle temporal gyrus (see Figure 2), with peaks in Brodmann Areas 21 and 40 [see Table 3]. We did not find any significant relationships between 18F-FDG uptake and CSF levels of sTREM-2.

Lastly, we performed linear regression analyses to assess the association between glial CSF biomarkers and metabolism in the specific Broadman Areas of interest.

Figure 3a shows regressions between β-S100 and 18F-FDG brain uptake in BA40 (R2 = 0.1593, F (1,27) = 4.737, p = 0.0392), BA21 (R2 = 0.1440, F (1,27) = 4.207, p = 0.0509) and the widened cluster of the parietal lobe (R2 = 0.1460, F (1,27) = 4.275, p = 0.0492).

Figure 3b shows the linear regression between CSF GFAP and 18F-FDG brain uptake in BA9 (R2 = 0.1806, F (1,27) = 5.069, p = 0.0342), BA11 (R2 = 0.1705, F (1,27) = 4.727, p = 0.0402) and BA6 (R2 = 0.0313, F (1,27) = 0.9420, p = 0.3419).

4. Discussion

Despite its widespread use in both clinical settings and basic research, the identity of the cell types contributing to 18F-FDG-PET signal is still debated. Traditionally, 18F-FDG-PET signal has been attributed only to neuronal uptake, with hypometabolism being considered as a direct index of neuronal dysfunction—loss of neuropil, synapse, or functional impairment—or death. However, evaluating glucose consumption in AD is made complex by other additional factors, including changes in the expression of glucose transporters (GLUT)

org/index.html, accessed on 1 January 2023). As suggested by Bennett et al., sPM t-maps were calculated for multiple comparisons using the false discovery (p < 0.05) and corrected for multiple comparisons at the cluster level (p < 0.001).

The level of significance was set at 100 (5 × 5 × 5 voxels, i.e., 11 × 11 × 11 mm) contiguous voxels. The voxel-based analyses were performed in the subgroup of patients using regression analyses. We designed independent models assessing the effects of each CSF biomarker (levels of GFAP, sTREM-2 and βS100) as regression factors—independent variables—on cortical 18F-FDG uptake, using age and sex as covariates, as well as t-tau levels in order to adjust for another marker of neurodegeneration. Positive and negative associations were tested in all cases.

The cluster obtained in the regression analysis was then exported by means of the WFU Pickatlas tool implemented in SPM 12. Specifically, the mean signal intensities calculated from each cluster within each subject were normalized to the average intensities of the Pons volume of interest. The use of normalization based on activity in the pons, rather than whole-brain counts as in the reference region, has been reported to result in greater accuracy in discriminating patients from controls in neurodegenerative diseases. As previously suggested by Pagani and colleagues), a dataset of normalized 18F-FDG values relevant to the cluster under study was exported. To determine whether the normalized 18F-FDG values for the studied cluster were Gaussian distributed, the D’Agostino K-squared normality test was applied (with the null hypothesis being normal distribution). We then performed linear univariate regression analyses using GraphPad Prism© version 9.3.1 for Windows (GraphPad Software, San Diego, California USA, www.graphpad.com, accessed on 1 January 2023) to visualize significant findings, namely the association between CSF glial biomarkers and normalized continuous data representing metabolism in the specific Broadman Areas of interest.

3. Results

First, we retrieved a trend of positive association between 18F-FDG uptake and CSF levels of GFAP in the right frontal-medial and precentral gyri (

levels of Glial Fibrillary Acidic Protein (GFAP)—the main intermediate filament protein in mature astrocytes— and β-S100, a calcium-binding protein tied to neurotoxic astrocytic activity. In a recent work, we ourselves investigated these CSF correlates of microglial and astrocytic activation, namely CSF sTREM-2, GFAP and β-S100, with our results supporting a dynamic switch in microglial functions, from neuroprotective to neurotoxic, depending on disease stage and APOE genotype, and a tight association of microglial activity with astrocytic reactivity, and with the acquisition of a more neurotoxic astrocytic phenotype (in this study).

The importance of the glial compartment has also been validated by recent studies highlighting the contribution of astrocytic metabolism to 18F-fluorodeoxyglucose (18F-FDG) uptake during Positron Emission Tomography (PET) scans. Strong evidence supports the hypothesis that glutamate recycling in astrocytes activates aerobic glycolysis, with neurons being partially fueled by lactate derived from astrocytes, and astroglial glutamate transport triggering glucose uptake by astrocytes. On the other hand, microglial cells have been shown to consume more glucose than neurons and astrocytes, and their activation state has likewise been linked to FDG-PET alteration in AD mouse models and AD patients. This leads to speculation that microglial and astrocytic activity might shape patterns of regional hypometabolism of 18F-FDG-PET and, hence, cognitive manifestations of AD, proving the relevance of investigating the associations between astrogliosis, microgliosis and cortical metabolism.

Previous works also investigated the relationship between measures of cerebral glucose consumption and some markers of neuroinflammation, focusing especially on pre-symptomatic or very early AD, highlighting the presence of higher 18F-FDG-PET uptake in relation to neuroinflammatory processes in early AD. We aimed to implement these findings by evaluating a cohort of symptomatic patients diagnosed with sporadic AD, by exploring possible correlations between regional hypometabolism of 18F-FDG-PET and changes in CSF biomarkers of microglia
```

</details>

## 13. `bc2a02ac`

**Question.** What proportion of actively demyelinating multiple sclerosis lesions contained CHIT1-positive cells, and what was found in inactive lesions?

**Reference answer.** 95.2% of actively demyelinating lesions contained CHIT1+ cells (20 of 21), while none of the inactive lesions contained any (0 of 8).

**Answer under review.**

> 95.2% of actively demyelinating lesions contained CHIT1+ cells, whereas none of the inactive lesions contained any CHIT1+ cells.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
corrected P = 0.33). Nevertheless, we did find CHIT1 to be significantly enriched in cells positioned at pseudotime 7.5 (two-sided Wald test = 40.54, Benjamini-Hochberg-corrected P = 5.01 ×10−4). Moreover, CHIT1 expression was significantly associated with pseudotime in lineage 3 (two-sided Wald test = 123.29, Benjamini-Hochberg-corrected P = 5.92 ×10−17; Fig. 6C, Supplementary Data 6) and peaked as pseudotime passed through cluster MG4 (Fig. 6). To sum up, pseudotime trajectory analysis indicated that CHIT1 expression accompanies the transition of microglia towards a more activated, MS-associated cell state.

Neuropathological evaluation shows phagocytic CHIT1+ cells in actively demyelinating lesions

To validate our transcriptomic results at the protein level, we performed neuropathological evaluation of brain tissue from 5 acute monophasic MS, 1 RRMS, 3 primary progressive (PPMS) and 3 secondary progressive (SPMS) MS patients. A total of 8 inactive and 21 active (including 2 chronic active or smoldering) MS lesions were analyzed (Supplementary Table 8).

Immunohistochemical staining of MS brains showed that CHIT1 was absent in normal-appearing white matter (NAWM, Supplementary Fig. 6). Where 95.2% of actively demyelinating lesions contained CHIT1+ cells (20/21), none of the inactive lesions contained any CHIT1+ cells (0/8). We did not only observe CHIT1+ cells in active lesions of more late-stage MS patients (RRMS, PPMS and SPMS with a disease duration up to ±34 years), but also in acute (monophasic) MS patients (disease duration of 0.2-5 months) – confirming the presence of CHIT1 already early in the disease course. Of the two smoldering lesions, that only have an active lesion edge, one contained few CHIT1+ cells, whereas the other lacked CHIT1 immunoreactivity.

Immunofluorescent multiplex labeling confirmed that ionized calcium-binding adapter molecule 1-positive (Iba1+) and transmembrane protein 119-positive (TMEM119+) microglia do not express CHIT1 in

CHIT1 secretion by microglia/macrophages in MS effectively counteracts the deposition of chitin-like compounds, whereas in severe Alzheimer’s disease this clearance is more imbalanced. Alternatively, CHIT1 production in the absence of chitin might also represent an ancient remnant of microglia/macrophage activation as genes for chitinases are highly evolutionary conserved,.

One of the principal challenges for the development of glial biomarkers in MS has been cellular specificity. Several CSF and serum biomarkers of myeloid cell activity in MS are under investigation (e.g. CHI3L1, soluble CD163 and osteopontin). However, these biomarkers do not sufficiently distinguish between CNS-resident microglia and monocyte-derived macrophages, which complicates their applicability since microglia and macrophages might effectuate different roles in MS. Here, our transcriptomics showed that CHIT1 expression is largely restricted to microglia and accompanies their transition towards a more activated, MS-associated cell state. After the CHIT1+ cluster MG4, our microglial trajectories diverged towards the ‘MS-associated’ clusters (MG5 and 6) on the one hand and the ‘pre-activated’/‘pro-inflammatory’ clusters (MG8 and 9) on the other hand. This trajectory pattern suggests that homeostatic microglia upregulate CHIT1 when they start to get activated and involved in lipid clearance. However, CHIT1 expression appeared to wane again in most microglia when they start to develop a disease-/MS-associated phenotype, possibly instigated by unrelenting inflammatory cues and/or persistent lipid phagocytosis and accumulation. The second direction towards ‘pre-activated’/‘pro-inflammatory’ clusters might reflect microglia present in the MS brain that obtain a more general activated, inflammatory profile, possibly as a form of bystander activation, although more in-depth functional analyses of these cells are needed to confirm such hypotheses. Neuropathological evaluation showed that small CHIT1+ cells with limited PLP uptake were Iba1+ and TMEM119+ and were mostly situated towards the lesion edge, whereas this Iba1 and TMEM119 immunoreactivity was absent on larger, foamy CHIT1+ cells located more

Introduction

Multiple sclerosis (MS) is a chronic autoimmune disorder of the central nervous system (CNS) characterized by considerable interindividual heterogeneity in terms of disease onset and severity. Despite continuous scientific advancement, accurately predicting long-term outcomes and effectively stratifying treatment regimens based on uncertain prognosis remain major challenges in MS care. Clinicians thus face an unmet need for disease activity measures with proven prognostic value. In particular, very few blood and cerebrospinal fluid (CSF) biomarkers have yet found translation into clinical practice.

Over the past few years, the role of innate immune cells such as CNS-resident microglia and monocyte-derived macrophages in MS pathogenesis has gained increased attention–. Microglia are anticipated to provide novel strategies in the development of biomarkers for MS disease activity. Previous work from our group showed that among several myeloid markers, CSF concentrations of chitotriosidase or chitinase 1 (CHIT1) at diagnostic lumbar puncture best reflected disability status at a median of five years later. Only few other studies have evaluated CHIT1 concentrations in relation to MS prognosis,. However, these studies – as our previous work – were limited to single-time-point disability assessments. In addition, CHIT1 has been found to be upregulated in chronic active MS lesions at the bulk RNA level, whereas its expression was largely undetectable in chronic inactive lesions and in brain tissue from non-neurological controls,. Nevertheless, since variations in biomarker concentrations must ultimately be coupled to disease processes to be clinically relevant, unraveling cell-type specificity of CHIT1 and the functional state of CHIT1-expressing cells in MS remains a prerequisite. This is emphasized by the functional diversity and cellular heterogeneity of microglia and CNS-associated macrophages uncovered in recent work–.

In this work, we investigate five microglia/macrophage-related proteins – CHIT1, chitinase-3-like protein 1 (CHI3L1, also known as YKL-40), soluble triggering receptor expressed on myeloid cells 2 (sTREM2), glycoprotein non-metastatic melanoma protein B (GPNMB) and C-C motif chemokine ligand 18 (CCL18) in the CS

away from the lesion edge, suggesting that CHIT1+ microglia start to lose certain surface markers in the process of PLP accumulation. TMEM119 is one of the main homeostatic microglia markers that is not expressed on monocyte-derived macrophages and has been shown to be downregulated in active MS lesions and other inflammatory conditions of the brain–. Moreover, decreased Iba1 expression and even Iba1- microglia have previously been described in neurodegenerative disorders such as Huntington’s and Alzheimer’s disease. Keren-Shaul and colleagues showed that DAMs found in a mouse model of Alzheimer’s disease were characterized by downregulation of AIF1 (the gene encoding for Iba1) as well as homeostatic genes such as TMEM119 and P2RY12.

Although relapsing and progressive MS are classified as distinct clinical phenotypes, the field now increasingly recognizes that the clinical course of MS is a continuum, where both inflammatory and neurodegenerative processes co-exist in a spectrum. Moreover, it is known that activation of CNS-resident microglia already occurs early in the disease. Indeed, most phagocytes initially present in active MS lesions are microglia, and with lesion maturation, more macrophages will infiltrate from the blood. As MS shifts towards a more progressive phase, microglia are once more involved in the slow expansion of chronic active lesions. Our work suggests that already early in the MS disease course CHIT1 is secreted into the CNS parenchyma by activated microglia who lost their homeostatic signature as these cells start to accumulate myelin debris. Conceivably, interstitial CHIT1 consequently ends up in the CSF via the glia-lymphatic or ‘glymphatic’ system in which CSF mixes with the interstitial fluid to wash away extracellular waste, as has been described for β-amyloid,. Elevated CSF CHIT1 concentrations at diagnosis thus likely identify MS patients who already at the start of their disease present with significant CNS pathology – i.e. more extensive microglial activation – and are at greater risk for faster disability progression. As of now, apart from some clinical parameters such as baseline EDSS, older age at diagnosis and spinal cord lesions, MS clinicians are equipped with few predictors for disability progression at time of diagnosis. Therefore, a fast-
```

</details>

## 14. `6f1f024d`

**Question.** What did adapting the Clinical Dementia Rating scale for adults with Down syndrome achieve with respect to the distribution of decline scores?

**Reference answer.** It captured a range of cognitive decline and shifted the distribution of decline scores toward lower or no impairment, by adjusting the original questions for premorbid intellectual and functional ability.

**Answer under review.**

> Adapting the Clinical Dementia Rating scale for adults with Down syndrome shifted the score distribution toward no/low impairment when adjusting for premorbid function, as shown in Figure 2. This adjustment was particularly pronounced, moving nearly the entire sample from indicating at least very mild dementia to no dementia.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
In addition to these advances, it would be desirable to adapt clinical staging instruments that are widely utilized in scientific and clinical work involving AD dementia in the broader population to afford comparability of assessment and staging for scientific and clinical efforts involving individuals with DS. Therefore, we adapted the Clinical Dementia Rating scale (CDR) for use in DS. The CDR is a semi-structured clinical diagnostic interview that is an integral component of the Uniform Data Set that is used by all federally funded Alzheimer Disease Centers (ADC) to determine the presence or absence of dementia for individuals being evaluated at ADCs. The semi-structured interviews are administered separately to an informant and then to the research participant or patient and focus on capturing intra-individual change from previous cognitive and functional performance levels. An experienced clinician then synthesizes the information from the interview to determine the presence or absence of dementia and, when present, its severity. A CDR score of 0 indicates cognitive normality, whereas scores of 0.5, 1, 2, and 3 indicate very mild, mild, moderate, and severe dementia, respectively.

The primary goal of this project was to determine whether adaptations of the CDR for DS—by both interview and caregiver report—could reliably capture variation among DS patients when implementing new adaptations of an established dementia rating scale.

Methods

Sample

In the first study phase, families with DS adults aged 18 years and older were recruited from the St. Louis ARC, a non-profit organization that provides support and services for individuals with intellectual and developmental disabilities in the St. Louis region. Potential participants were recruited via letters sent to the families by St. Louis ARC. A total of 189 letters were sent asking families to contact the study. Forty families (21.2% response rate) contacted study staff over the telephone regarding their interest to participate. Verbal consent was obtained from the caregiver over the telephone and he/she was then sent the questionnaire version of the modified CDR instrument (CDR-QDS) by postal mail. All forty CDR-QDS instruments that were mailed were received back for evaluation.

Figure 1 shows the distribution of summary CDR-QDS scores (n = 34); the sample manifested a wide range of scores. The distribution was skewed toward lower scores where 13 individuals had a score of 0 (38.2%), and another 10 individuals had scores of 1 or 2 (29.4%). CDR-QDS summary score mean was 4.85 (SD = 7.29, median = 1, range 0–23, maximum possible score = 32). There were three individuals with CDR-QDS scores ≥ 20, all of whom were over the age of 30 years.

Figure 2 shows the distribution of CDR-IDS sum of boxes (upper panel), global (middle panel), and dichotomized global scores (lower panel) (n = 22) when scores were adjusted for premorbid function (adjusted) and not adjusted (unadjusted), which would be consistent with current function. As predicted, adjusting for premorbid ability shifted, in the non-pathological direction, scores that would otherwise be elevated on the standard version of the CDR. CDR-IDS adjusted sum of boxes sample mean was 1.68 (SD = 3.90, median = 0.5, range 0–16, maximum possible score = 18) and unadjusted mean was 4.41 (SD = 3.88, median = 3, range 0.5–16). The table embedded in the middle panel of Fig. 2 shows the extent to which adjustment for premorbid ability shifted individuals to lower global CDR-IDS scores. For example, of the 13 DS adults with adjusted global CDR-IDS scores of 0, 10 had unadjusted scores of 0.5. The shift from any severity of dementia (CDR-IDS > 0) to no dementia (CDR-IDS = 0) is most pronounced in the lower panel, where nearly the entire sample (21 of 22 DS adults) meets criteria for at least very mild dementia before score adjustment, but only 9 individuals meet the dichotomized dementia threshold after score adjustment.

Relationship of age and IQ to CDR-QDS and CDR-IDS

The modified CDR questionnaire (CDR-QDS) and interview (CDR-IDS) instruments capture a range of impairment in DS adults. Adjustment of cognitive decline scores for premorbid function dramatically shifted the score distribution toward no/low impairment and was an important element in identifying DS adults with suspicion for dementia. The DSDS indicated high suspicion of dementia in two of twenty-two individuals in this sample who had broadly elevated scores on the modified CDR instruments. The modified CDR instruments captured a range of subthreshold impairments in cognitive function that may prove extremely useful in prospective studies of the development of AD in DS. Moreover, future research is warranted to use quantitative scales such as these to help differentiate dementia from other neuropsychiatric problems in DS, including catatonia, adjustment disorder, and a range of psychiatric comorbidities, all of which are potentially treatable and for which inappropriate/premature assignment of a diagnosis of dementia may be extremely misleading and result in a major obstacle to appropriate care and treatment. For DS adults with elevated scores for cognitive impairment in this study, the impairment generally encompassed multiple cognitive domains and was not predominantly within the memory domain, as seen in the typical population.

Higher IQ was related to lower levels of cognitive decline. In the typically developing aging population, greater “cognitive reserve,” a measure that combines IQ, education, and lifelong engagement in cognitive activities, is also related to lower cognitive decline. Here, we show a relationship in the lower distribution of IQ scores assessed using a single task.

Inclusion of the DSDS was meant to serve as an external validity index, but our sample did not reveal sufficient variability in DSDS scoring, and it is notable that a wider range of scores were elicited among the subjects using the CDR instruments. The vast majority of the sample was rated as having no dementia on the DSDS, but most had non-zero CDR-QDS and CDR-IDS scores; the 2 individuals flagged for reassessment or rated as early dementia on the DSDS had higher CDR-QDS scores, as well as CDR-IDS adjusted global scores consistent with moderate and severe dementia. The DSDS was developed and validated in a community sample of individuals the majority of whom had severe to profound intellectual disability which could result in low sensitivity of the DSDS in detecting dementia in higher functioning individuals. We note that in another instrument, the DSQIID, has been adapted by the National Task Group (NTG) on Intellectual Disabilities and Dementia Practices as an Early Detection Screen for Dementia (NTG-EDSD), for wide use in dementia screening. Our results using comparable methods in the questionnaire version of the CDR support the utility of questionnaire-based screening, and future studies should continue to explore the utility of combining caregiver screening and direct observation in identifying dementia in DS and distinguishing it from other neuropsychiatric impairments that can result in cognitive decline in DS, most notably, catatonia, which is rare and controversial, but is treatable and may assist clinicians in avoiding a false designation of dementia on the basis of observations or ratings that suggest cognitive decline, especially in younger adults with DS.
```

</details>

## 15. `56c60f52`

**Question.** In rats transgenic for human mutant tau, how did microglial numbers at 10 months compare with controls, and what had changed by 18-20 months?

**Reference answer.** At 10 months there were no differences in microglial numbers between transgenic and control rats; by 18-20 months the microglia showed extensive proliferation and an activated phenotype.

**Answer under review.**

> At 10 months of age, the number of microglia in R962-hTau rats was comparable to that seen in control animals. In contrast, dramatic increases in the number of microglia in the subiculum, CA1, and the hilus of the dentate gyrus were observed in 18–20-month-old transgenic rats.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
In summary, this study supports the idea that rats transgenic for full-length human mutant tau are promising models, particularly, for studying the spatio-temporal progression of tau pathogenesis and how it relates to neurodegeneration. In this regard, this model has shown that tau aggregation lies upstream, followed by the sequestration of endogenous tau, microglia proliferation, reactive astrocytes, myelin abnormalities, neuronal loss, ventricular dilation, brain atrophy, concurrent with development of memory and learning deficits. It highlights that rat brains show resilience to the initial tau pathology and that marked cognitive impairments are coincidental with advanced tau pathology and neurodegeneration, a situation resembling the evolution and clinical presentation of AD and other tauopathies.

At 10 months of age, the number of microglia in R962-hTau rats was comparable to that seen in control animals. In contrast, dramatic increases in the number of microglia in the subiculum (p =.0002), CA1 (Fig. 5A; p <.0001) and the hilus of the dentate gyrus (p <.0001) were observed in 18–20-month-old transgenic rats (Fig. 5C).

Some microglial cells were seen to localise around AT8-immunopositive neurons (Fig. 5A, centre panel inset), however, there were no differences in microglial numbers at 10 months of age between transgenic and controls rats (Fig. 5B). At later time points (18–20-months), along with extensive proliferation (Fig. 5C), microglia displayed an activated phenotype (Fig. 5D). Additionally, some microglia adopted a distinct, rod-like phenotype, which has previously been described in AD patients and in experimental models of traumatic brain injury. Rod-like microglia ran parallel, either individually or in trains (Fig. 5E), to neuronal projections from the fascioloa cinerea, subiculum, CA1 and layers III and V of the primary somatosensory and entorhinal cortices respectively.

Alterations in astrocytic GFAP expression were also quantified at 10 and at 18–20 months of age. No differences were observed at 10 months when compared with age-matched controls (Fig. 5F, G). However, increases in GFAP total fluorescence and fluorescence area was observed in CA1 and the molecular layer of the dentate gyrus at 18–20-months (Fig. 5F, H).

Extensive myelin degeneration occurs in aged R962-hTau rats

3.6

To determine if a loss of white matter was associated with the degeneration in grey matter, we stained tissue sections with Luxol Fast Blue. This revealed demyelination in the corpus callosum of transgenic rats when compared with control animals at 18–20-months, indicating this pathology occurs secondary to upstream tau aggregation (Fig. 5I).

To assess if behavioural deficits correlated with human tau levels, we compared the immunofluorescence HT7 signals across regions of interest (CA1, CA3, hilus, amygdala cortex and basomedial nuclei, somatosensory cortex) with each rats' cognitive index score, representing a composite of their performance across all cognitive tests, and brain volume in the same region (Supplementary Fig. 11). While human tau levels did not correlate with cognitive indices [Supplementary Fig. 11B; r = 0.16, p =.70 (NS)], they did correlate with brain volume in the same region (Supplementary Fig. 11C; r = 0.82, p =.012). At 18–20 months of age animals with less intense HT7-immunoreactivity generally had greater brain atrophy and less intense inclusions (Supplementary Figs. 3 and 11A). The same association was present for levels of endogenous tau (T49) across the regions of interest (Supplementary Fig. 11D). T49 levels in R962-hTau rats did not correlate with cognitive index [Supplementary Fig. 11E; r = −0.001, p =.99 (NS)], but positively correlated with brain volume (Supplementary Fig. 11F; r = 0.77, p =.027). These results likely reflect a reduction of brain tau levels following neuronal loss.

Discussion

4

In this report, we describe the production and characterisation of the first rat line transgenic for full-length human tau with the P301S mutation. We demonstrate the progressive, age-dependent increase in the accumulation of filamentous tau, which was upstream of neurodegeneration, myelin abnormalities, gliosis and behavioural deficits. In contrast to the transgenic mouse model where human P301S tau forms filamentous aggregates, aggregates of the R962-hTau rats comprised both human transgenic tau as well as endogenous rat tau in older timepoints.

In order to characterise alterations in brain volume and structure, we performed morphometric analysis of coronal brain sections (Fig. 4A, Supplementary Fig. 8B). By 18–20-months of age, we found an increase in ventricle size (p =.001), a decrease in brain volume in the frontal cortex (p =.001) and hippocampus (p =.0057) (Fig. 4B). Brain atrophy and ventricular dilation were not observed in R962-hTau rats at the 10-month time point, despite progressive tau pathology (Fig. 4A). No interaction between sex and genotype for ventricle volume was observed [Genotype:Sex interaction, p =.48, not significant (NS)]. To confirm the histological observations of ventricular dilation and brain atrophy, we performed an MRI analysis of an individual rat at 15 months of age (Fig. 4C), which confirmed in vivo these prominent anatomical alterations akin to overall consequences of tauopathy in the human.

Given the alterations in brain structure, we counted the number of NeuN-immunoreactive nuclei in the hippocampus (Fig. 4D, E). No differences were observed in the 10-month-old cohort in layers CA1 and CA2. However, in transgenic rats aged 18–20-months, we observed an extensive loss of neurons throughout CA1 (p <.0001) and CA2 (p <.0001) (Fig. 4E).

Activation of microglia and astrocytes in regions with tau pathology

3.5

We investigated whether alterations in glial cell numbers and morphology occurred in R962-hTau rats. We used antibodies against microglial/macrophage ionized calcium-binding adapter molecule 1 (Iba1), and the astrocyte-specific protein, glial fibrillary acidic protein (GFAP).

Tau transgenic mice have been more frequently used and recapitulate, to varying extents, important disease features. Among the most commonly used models are those with the P301S and P301L mutations, including 0N4R P301S, PS19 and Tg4510 models which develop hallmarks of tauopathy, including neuronal loss, gliosis and cognitive impairment. However, behavioural deficits occur relatively early in across these models, opposing the relatively late development of cognitive impairments in humans. Additionally, many fail to develop a marked, human-like, brain atrophy and significant ventricular dilation. In this regard, the PS19 mouse model achieved these features after the co-expression of P301S mutant tau and human ApoE3 and ApoE4 isoforms. The closer genetics and physiology of rats to humans may enable a more in-depth analysis of the key events marking the progression of tau pathology and how they relate to cognitive impairment and neurodegeneration. Evidence indicates that endogenous rat ApoE may be functionally more similar to human isoforms, and has a structural homology of 73.5% and 73.9% with ApoE3 and ApoE4 respectively. This may be significant for a more faithful recapitulation of human tauopathy in rat models, models which may be more suitable to experimental therapeutics with better possibilities of clinical translations.
```

</details>

## 16. `f69b5225`

**Question.** Which periodontal pathogen was confirmed by PCR among the live bacteria found in mouse brains, and what did that finding support?

**Reference answer.** F. nucleatum; its presence supports the concept of a natural living microbial presence in the brains of mice, that is, a natural brain microbiome.

**Answer under review.**

> The periodontal pathogen F. nucleatum was confirmed by PCR among the live bacteria found in mouse brains, and this finding supported the idea of a natural brain microbiome.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
Importantly, in a slightly different oral infection mouse model, we found the presence of whole live oral bacteria present in fresh mouse brains from both control and infected mice (Additional file 2: Figure S2). Furthermore, we used PCR validation to confirm that one of the live bacteria present in the brains, included a periodontal pathogen, namely, F. nucleatum. This speaks to the idea of a natural living microbial presence in the brains of mice and supports the concept of a natural brain microbiome.

Using a slightly different mouse model from the model described above, with the only difference being that these mice were orally inoculated with T. denticola (ATCC 35405), fresh brain specimens from these mice were sampled with swabs to attempt to grow out whole living bacterial microbes using a sterile technique/environment. For this purpose, brain samples were dissected and cut in half in a sagittal plan, then swab samples were collected from the inner area of the left and right halves of the brain and the whole brain. These swab samples were grown on Oral Treponeme Enrichment Broth media anaerobically at 37 ºC for 72 h. Subsequently, turbid media, indicating bacterial growth, was sampled and checked by PCR for bacterial growth of 4 periodontal pathogens [T. denticola, P. gingivalis, F. nucleaturm, T. forsythia as measured by PCR using TaqMan primers and probes (Invitrogen) corresponding to the 16S rRNA gene as in our previous study]; revealing the detection of F. nucleatum in the samples from the left half of the brain. Subsequently the samples from the left half of the brain were plated on BHI agar plates (Anaerobe systems, CA) for 72 h. Individual colonies were randomly selected from the plates and expanded for another 72 h in BHI media. DNA was isolated from these bacterial broth samples and checked for the presence of the four specific periodontal pathogens (T. denticola, P. gingivalis, F. nucleaturm, T. forsythia).

Microbiome analysis of brain tissues via 16s rRNA sequencing

To further assess the presence of periodontal bacteria in the brain tissues, the number of periodontal pathogens was measured in the brain samples using RT-PCR in a manner of absolute quantification. The detection frequency of the four periodontal pathogens is shown in Fig. 3A. P. gingivalis could be detected in all four groups with different frequencies. T. forsythia was detected in the infection, nisin, and nisin + infection group, but not in the control group. F. nucleatum was detected in the infection, nisin + infection group, but not in the control and nisin group. The presence of T. denticola was not detected in any of the groups. The copy number for P. gingivalis in the control group was significantly lower than that in the infection group (P < 0.05) (Fig. 3B). Although the P. gingivalis copy number was lower in the infection + nisin group than in the infection group, this did not reach statistical significance (Fig. 3B). However, nisin treatment significantly reduced the T. forsythia copy number in the infection + nisin group compared to the infection group (P < 0.05) (Fig. 3C). Interestingly, the F. nucleatum levels were higher in the infection + nisin group than that in the infection group, but the difference was not statistically significant (Fig. 3D). When taken in aggregate, the copy numbers for T. forsythia were highest among all 4 pathogens in the infection group (Fig. 3E).

Using a slightly different mouse model with only a T. denticola infection and utilizing a sterile technique and environment, we were able to isolate whole living bacteria from the fresh brains of both control and infected mice. Using PCR validation we confirmed the presence of F. nucleatum in the fresh brains of the mice (Additional file 2: Fig. S2).

Oral polymicrobial infection/periodontal disease induces neuroinflammation in the brain and nisin reverses the change

Over the last decade, a growing body of scientific evidence has demonstrated that alterations in the oral microbiota play an important role in the initiation and progression of AD. Oral microbiota could be transported to the brain through the blood stream in patients with periodontitis. Among the oral microorganisms, P. gingivalis, T. forsythia, F. nucleatum and T. denticola have been implicated in the development of AD. P. gingivalis is the most documented periodontal pathogen in AD-related studies. The presence of P. gingivalis and its virulence factors, including lipopolysaccharide and gingipains, were confirmed in this context in both human and animal studies. In the present study, P. gingivalis DNA was detected in all six mice in the infection group, which further confirmed the translocation of P. gingivalis components from oral cavity to the brain. However, P. gingivalis was also detected in four of the six control mice at the conclusion of the study. There could be several reasons for this observation. We and others have previously shown that mice carry P. gingivalis in the oral cavity, thus this may be the source of the brain P. gingivalis signal in the control mice, despite our initial antimicrobial washout period. Another reason for this result may be that the mice were not housed in a gnotobiotic or specific pathogen free (SPF) grade facility, and thus there may have been potential environmental contamination; although the animals had an initial antimicrobial wash out period. However, the quantitative PCR results showed that the number of P. gingivalis copies in the infection group were significantly higher than that in the control group, indicating that oral infection did result in an increased load of P. gingivalis DNA in the brain tissues. In contrast, T. denticola was not detected in the brain samples in our study, which is inconsistent with former studies. Miklossy first proposed that some spirochetes derived from the oral cavity were associated with AD. Riviere et al. further demonstrated that several types of oral Treponema species, including T. denticola have been found in AD brain samples. In our previous study, we found that it was relatively hard for T. denticola to colonize the oral cavity compared with the other three bacteria.

Growing evidence from cross sectional and longitudinal studies have demonstrated an association between AD and infectious conditions, such as periodontal disease. The presence of periodontal pathogens, such as Porphyromonas gingivalis and Treponema species, have been found in post-mortem brain tissues of AD patients. In addition, animal studies have been conducted to determine the effects of periodontitis on pathogen translocation and possible effects on the brain. Periodontal pathogens and their molecules have also been reported in the brain. Overall, these findings strengthen the hypothesis that periodontal pathogens play an important role in the development of AD. Periodontal disease and its characteristic oral microbial dysbiosis are thought to contribute to neuroinflammation and amyloid protein production via translocation of periodontal pathogens and their components to the brain. This hypothesis is further supported by research linking the presence of periodontal microorganisms with increased Amyloid β deposition, tau hyperphosphorylation, and glial cell inflammation and activation [–]. A recent study showed that treatment with a gingipain inhibitor reduced P. gingivalis infection in the brain of mice and prevented further neurodegeneration and accumulation of pathologic plaques, suggesting that controlling periodontal infections and microorganisms may be an effective way to slow down the development of AD.

Despite this compelling evidence for the presence of bacteria in the brain supporting the concept of a brain microbiome, there is considerable debate that a brain microbiome exists in healthy individuals. Currently the evidence for the infection of the brain in mouse studies is based on detection of bacterial products, including DNA, RNA, LPS and surface proteins, yet microbiome sequencing studies have not been performed. Here, we examine the presence of a brain microbiome using a genomic method-driven approach.
```

</details>

## 17. `7c4bbb7e`

**Question.** Did COL6A2 co-localize with the deposits in prion-protein cerebral amyloid angiopathy tissue, and where was it located instead?

**Reference answer.** COL6A2 did not generally co-localize with the deposits despite co-occurring in largely the same vessels; it localized more internally, as a component of the basal membrane.

**Answer under review.**

> COL6A2 did not generally co-localize with the deposits but instead localized more internally as a component of the basal membrane.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
The PrP-CAA tissue was confirmed negative for Aβ pathology (Fig. 7k) and showed positive for Prp (data not shown). NDP immunoreactivity was highly increased and localised to the affected vessels. NDP staining was more pronounced around affected capillaries than at affected larger vessels. COL6A2 immunoreactivity was clearly present around capillaries and larger affected vessels, of which the vascular pathology was clearly observed using haematoxylin. Although co-occurring in largely the same vessels COL6A2 did not generally co-localize with the deposits, but instead localized more internally as a component of the basal membrane. APOE and APCS were also highly present and co-localized with the Prp deposits.

In the white matter no immunoreactivity was seen for Aβ or any of the marker proteins (Fig. 7p-t) in the control case. The CADASIL case showed characteristic pathology in the white matter, thickened vessel walls, in the white matter as is common with this condition. No Aβ pathology was present (Fig. 7u) Mild immunoreactivity for NDP was present and of the assessed proteins COL62A staining was most pronounced. APOE and APCS also displayed mild immunoreactivity related to the affected vessels (Fig. 7v-y).

In hypertension related small vessel disease the presence of COLA6A2 was most prominent while immunoreactivity for NDP, APOE and APCS was low but present (Fig. 7z-ad). Interestingly IHC analysis of the CARASAL cases showed only the prominent presence of COL6A2 in affected vessels while NDP, APOE and APCS were absent.

Taken our data together, from the tested panel of proteins, we recognize COL6A2 as a general small vessel disease marker. NDP, APOE and APCS are most prominent in CAA (type-1 and cotton wool) and Prp-CAA. Involvement of NDP, APOE and APCS in other small vessel diseases is varying from non (CARASAL) to mild (CADASIL). Importantly, NDP is explicitly suitable to evidently separate CAA from Aβ plaque pathology (Table 4).[TABLE: Table 4]

Discussion

Immunoreactivity for COL6A2 is equally present in leptomeningeal vessels in control, AD and CAA tissue. (TIF 3794 kb) Additional file 9:Figure S8. Immunohistochemistry of Amyloid-beta, NDP, COL6A2, APOE and APCS on multiple brain regions of a HCHWA-D CAA type-1 case. Brain tissue of a case exhibiting a hereditary form of CAA type-1 was analyzed by immunohistochemistry of Amyloid-beta, NDP, COL6A2, APOE and APCS. Aβ pathology was confirmed and immunoreactivity associated with CAA type-1 pathology was found present for all markers. Scale bar in upper left picture represents 100 μm. (TIF 34988 kb)

COL6A2 IHC showed some immunoreactivity in control and AD cases which was restricted to leptomeningeal vessels (Additional file 8: Figure S7) and a few large vessels in the brain tissue. In CAA type-1, immunoreactivity for COL6A2 was highly increased and includes brain capillaries and larger vessels. Immunoreactivity was mostly associated with the endothelium and/or the adventitia (Fig. 5g-i). Similar results were obtained using two different antibodies for COL6A2 (data not shown). HTRA1 IHC showed clear overlap with Aβ in both AD and CAA. Compact and diffuse staining was observed related to the vessels in the CAA cases and showed plaque pathology in the AD cases without CAA. Control cases were all negative for HTRA1 (Fig. 5j-l). IHC for APOE resulted in pronounced staining of the vasculature in CAA cases and appeared related to compact deposits as well as more diffuse dyshoric deposits. Also immunoreactivity of APOE was observed in the AD cases related to the Aβ plaques, although the staining was less intense than that related to the vascular amyloid in the CAA cases (Fig. 5p-r). APCS IHC illustrated the presence of this protein in relation with both diffuse and compact Aβ pathology in both the CAA and AD group. However, staining related to the plaque pathology was less intense than that related to the vascular Aβ pathology (Fig. 5m-o).

For quantification of the IHC, images were obtained at sites that, for the AD and CAA cases, had high Aβ pathological burden in nearby sections of the same tissue block. The percentage of positively stained pixels over a total of 5 images from each case was determined. Although this method is semi-quantitative, it allowed a region-specific analysis in line with the tissue obtained by laser capture dissection that was at the basis of the original mass spectrometry analysis. Using IHC quantification we observed strongly increased immunoreactivity in CAA type-1 cases for NDP and COL6A2, and moderate increases for APCS, HTRA1 and APOE, confirming the MS results (Fig. 6).

Specificity in relation to other small vessel diseases

To assess the specificity of Aβ, NDP, COL6A2, APCS and APOE in relation to other small vessel diseases we performed additional IHC on cases that present various types of vascular defects, i.e., cotton wool plaque pathology, prion CAA, cerebral autosomal dominant arteriopathy with subcortical infarcts and leukoencephalopathy (CADASIL), hypertension related small vessel disease and Cathepsin A-related arteriopathy with strokes and leukoencephalopathy (CARASAL). IHC was performed on sections that exhibited the relevant pathological characteristics of each disease including an additional CAA type 1 case. Immunoreactivity for Aβ, NDP, COL6A2, APOE and APCS was confirmed in the CAA type-1 case (Fig. 7a-e). Immunoreactivity for these proteins was also assessed and confirmed in case exhibiting hereditary cerebral haemorrhage with amyloidosis Dutch type (HCHWA-D), which is a heredity form of CAA-type-1 (Additional file 9: Figure S8).

In tissue with cotton wool plaques the pathology was confirmed using IHC for Aβ displaying pathology around capillaries and larger vessels with dyshoric changes extending deep into the parenchyma (Fig. 7f). Intense NDP immunoreactivity was observed related to capillaries and the dyshoric changes and to a lesser extend directly lining the larger vessels. COL6A2 showed intense immunoreactivity lining the capillaries and larger vessels (Fig. 7g). IHC for APOE and APCS presented a highly positive, staining that appeared similar to the Aβ staining.

Of the proteins described in Table 3 we selected APOE (approach A), NDP (approach B), HTRA1, APSC and COL6A2 (approach C), based on the fold change or specific expression in the CAA type-1 group compared to the AD and control groups, to confirm our mass spectrometry results. Immunoblotting was performed on whole tissue lysates of the same cases as used for the mass spectrometry analysis. When comparing the CAA group with the control group we found significant differences in NDP expression (Fig. 4). For APOE, APCS and COL6A2, the data showed the same trend of increased abundance in the CAA group as the proteomics data, but the differences did not reach significance. A likely explanation for this is the higher variation of expression of these proteins in the tissue used for immunoblotting, which in contrast to the mass spectrometry exploratory analysis, was not selectively enriched for pathological burden using LCM, and instead included white matter, leptomeningeal vessels and grey matter with a lower pathological burden. To unequivocally demonstrate CAA related expression, we turned to IHC analysis of these same proteins, which, in contrast to immunoblotting, allows region specific analysis similar to the LCM-LC-MS-MS analysis. For this a separate cohort was used consisting of cognitively healthy control cases (n = 8) without any Aβ or tau pathology, 2) AD cases with severe Aβ plaque pathology but no vascular deposits (no CAA) (n = 8) and 3) AD cases with severe CAA type-1 pathology (n = 6).
```

</details>

## 18. `b67cc8d7`

**Question.** Which plasma biomarkers contributed significantly to predicting both PACC and risk of Alzheimer's dementia, and what did plasma NfL appear more useful for?

**Reference answer.** Plasma P-tau217 and Abeta42/Abeta40 contributed significantly to the prediction of both PACC and risk of AD dementia, while plasma NfL added significant prognostic information for PACC and appeared more useful for predicting general cognitive decline and risk of all-cause dementia.

**Answer under review.**

> Plasma P-tau217 and plasma Aβ42/Aβ40 contributed significantly to predicting both PACC and the risk of Alzheimer's dementia. Plasma NfL appeared more useful for detecting non-AD-related neurodegenerative changes.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
all-cause dementia, thereby strengthening previous findings of plasma NfL as a general biomarker of neurodegeneration that detects non-AD-related neurodegenerative changes–.

We also compared plasma biomarkers directly against their corresponding CSF biomarkers. CSF biomarkers still appear to be superior to plasma biomarkers in terms of cognitive and clinical prognosis in elderly individuals without cognitive impairment, although this comparison was based on Akaike Information Criterion (AIC) values and there was in fact significant overlap in R2 between models. This indicates that CSF and plasma may provide similar predictive accuracy overall but that CSF provides a much more confident prediction with smaller confidence intervals. We hypothesize that this difference is largely based on the observation that CSF Aβ42/Aβ40 is a much stronger prognostic marker than plasma Aβ42/Aβ40. However, the discrepancy between plasma and CSF Aβ42/Aβ40 may not be biological but may instead be related to the performance of the specific plasma assays used here (Elecsys immunoassay). Our work in MCI patients showed a greater effect of plasma Aβ42/Aβ40 by using a mass-spectrometry method, indicating that a more effective plasma assay could lead to greater value. However, such data were not widely available in this cohort. Further work is needed to compare performance of CSF and plasma biomarkers in CU individuals using different assays, as recent studies suggest that the difference between CSF and plasma biomarkers is less pronounced in MCI.

Importantly, our results in terms of biomarker effect size did not change when we further took into account the main distinction of cognitively unimpairment—CN versus SCD. To note, both CN and SCD participants are both considered to be CU according to NIA-AA criteria. However, SCD participants in our study were followed in a memory clinic setting and had higher risk of developing AD dementia. Including this diagnostic distinction improved performance of the basic (demographics-only) model but did not alter the finding that plasma biomarkers provide significant prognostic information. Also, enriching for SCD status led to a significant reduction in trial sample size with AD dementia as outcome, but not with cognition as outcome. Since cognition is the main target of current AD trials, this indicates that enriching for SCD

of plasma NfL and a decreased effect of plasma Aβ42/Aβ40, while plasma P-tau217 remained a strong predictor (Supplementary Fig. 2; Supplementary Table 2). All biomarkers remained significant when combined together. Another sensitivity analysis in which we additionally adjusted for the effect of SCD on both baseline and change in cognitive resulted in a greatly increased baseline model fit (R2 = 0.17), while this did not affect the significance of any plasma biomarkers nor the significant improvement in model fit found by adding plasma biomarkers to the basic model (Supplementary Table 3). A comparison of model results between corresponding CSF and plasma biomarkers indicated that—in terms of AIC—CSF biomarkers had significantly better-combined prediction of PACC change than plasma biomarkers (AICΔCSF = −98 versus AICΔPlasma = −28; Supplementary Table 4).

Modeling clinical progression to AD dementia

We next tested whether plasma biomarkers were significantly associated with subsequent development of AD dementia. When added individually to a basic model consisting of age, sex, and education (Fig. 2), we found that plasma P-tau217 had the strongest association with conversion to AD dementia (HR = 3.54 increased odds/std., P < 0.0001), followed by plasma Aβ42/Aβ40 (HR = 2.00, P = 0.0002), while plasma NfL on its own did not add significant information to the basic model (HR = 1.51, P = 0.07). When combining all three plasma biomarkers together in the same model (Table 3), plasma P-tau217 (HR = 2.97, P = 0.0004) and Aβ42/Aβ40 (HR = 1.83, P = 0.003) remained significant. When adding APOE ε4 status to the set of demographic predictors, AUC values increased for all models, but all plasma biomarkers which were significant in the previous model remained significant when APOE ε4 status was added (Supplementary Table 5).[TABLE: Table 3]

All plasma biomarker-based models significantly improved prediction of 4-year conversion to AD compared to the basic model (AIC = 274; AUC = 0.64 [0.55, 0.77]; see Table 3). In terms of AIC, the

ers were significantly associated with cognitive decline as measured by the PACC. When added individually to a basic model consisting of age, sex, and education (Fig. 1), we found that plasma P-tau217 had the strongest association with longitudinal change in PACC (β = −0.20 points per year per SD increase in biomarker value, P < 0.0001), followed by plasma Aβ42/Aβ40 (β = −0.18, P = 0.0002), and plasma NfL (β = −0.16, P = 0.001). When combining all three plasma biomarkers together in the same model (Table 2), all three biomarkers remained significant (P = 0.004 for Aβ42/Aβ40, P = 0.002 for P-tau217, P = 0.01 for NfL). Adding APOE ε4 status to the basic model did not affect the significance of any biomarkers in either the combined or individual models (Supplementary Table 1), although the effect of plasma Aβ42/Aβ40 in the combined model decreased the most (β = −0.16, P = 0.002 with APOE ε4 status).[TABLE: Table 2]

All plasma biomarker models significantly improved prediction of PACC change compared to the basic model (AIC = 6699; R2 = 0.07, CI [0.06, 0.11]; see Table 2). In terms of AIC, a combination of all three plasma biomarkers predicted PACC change best (AICΔ = −28 versus basic model; R2 = 0.14 [0.12, 0.17], P < 0.0001), followed by plasma Aβ42/Aβ40 only (AICΔ = −14; R2 = 0.11 [0.09, 0.14], P < 0.0001), plasma P-tau217 only (AICΔ = −13; R2 = 0.09 [0.08, 0.13], P = 0.0002), and finally plasma NfL only (AICΔ = −9; R2 = 0.10 [0.08, 0.14], P = 0.002).

A sensitivity analysis in which longitudinal MMSE was used as the cognitive outcome showed an increased effect
```

</details>

## 19. `8b66207c`

**Question.** What proportion of actively demyelinating multiple sclerosis lesions contained CHIT1-positive cells, and what was found in inactive lesions?

**Reference answer.** 95.2% of actively demyelinating lesions contained CHIT1+ cells (20 of 21), while none of the inactive lesions contained any (0 of 8).

**Answer under review.**

> 95.2% of actively demyelinating lesions contained CHIT1+ cells, whereas none of the inactive lesions contained any CHIT1+ cells.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
corrected P = 0.33). Nevertheless, we did find CHIT1 to be significantly enriched in cells positioned at pseudotime 7.5 (two-sided Wald test = 40.54, Benjamini-Hochberg-corrected P = 5.01 ×10−4). Moreover, CHIT1 expression was significantly associated with pseudotime in lineage 3 (two-sided Wald test = 123.29, Benjamini-Hochberg-corrected P = 5.92 ×10−17; Fig. 6C, Supplementary Data 6) and peaked as pseudotime passed through cluster MG4 (Fig. 6). To sum up, pseudotime trajectory analysis indicated that CHIT1 expression accompanies the transition of microglia towards a more activated, MS-associated cell state.

Neuropathological evaluation shows phagocytic CHIT1+ cells in actively demyelinating lesions

To validate our transcriptomic results at the protein level, we performed neuropathological evaluation of brain tissue from 5 acute monophasic MS, 1 RRMS, 3 primary progressive (PPMS) and 3 secondary progressive (SPMS) MS patients. A total of 8 inactive and 21 active (including 2 chronic active or smoldering) MS lesions were analyzed (Supplementary Table 8).

Immunohistochemical staining of MS brains showed that CHIT1 was absent in normal-appearing white matter (NAWM, Supplementary Fig. 6). Where 95.2% of actively demyelinating lesions contained CHIT1+ cells (20/21), none of the inactive lesions contained any CHIT1+ cells (0/8). We did not only observe CHIT1+ cells in active lesions of more late-stage MS patients (RRMS, PPMS and SPMS with a disease duration up to ±34 years), but also in acute (monophasic) MS patients (disease duration of 0.2-5 months) – confirming the presence of CHIT1 already early in the disease course. Of the two smoldering lesions, that only have an active lesion edge, one contained few CHIT1+ cells, whereas the other lacked CHIT1 immunoreactivity.

Immunofluorescent multiplex labeling confirmed that ionized calcium-binding adapter molecule 1-positive (Iba1+) and transmembrane protein 119-positive (TMEM119+) microglia do not express CHIT1 in

Introduction

Multiple sclerosis (MS) is a chronic autoimmune disorder of the central nervous system (CNS) characterized by considerable interindividual heterogeneity in terms of disease onset and severity. Despite continuous scientific advancement, accurately predicting long-term outcomes and effectively stratifying treatment regimens based on uncertain prognosis remain major challenges in MS care. Clinicians thus face an unmet need for disease activity measures with proven prognostic value. In particular, very few blood and cerebrospinal fluid (CSF) biomarkers have yet found translation into clinical practice.

Over the past few years, the role of innate immune cells such as CNS-resident microglia and monocyte-derived macrophages in MS pathogenesis has gained increased attention–. Microglia are anticipated to provide novel strategies in the development of biomarkers for MS disease activity. Previous work from our group showed that among several myeloid markers, CSF concentrations of chitotriosidase or chitinase 1 (CHIT1) at diagnostic lumbar puncture best reflected disability status at a median of five years later. Only few other studies have evaluated CHIT1 concentrations in relation to MS prognosis,. However, these studies – as our previous work – were limited to single-time-point disability assessments. In addition, CHIT1 has been found to be upregulated in chronic active MS lesions at the bulk RNA level, whereas its expression was largely undetectable in chronic inactive lesions and in brain tissue from non-neurological controls,. Nevertheless, since variations in biomarker concentrations must ultimately be coupled to disease processes to be clinically relevant, unraveling cell-type specificity of CHIT1 and the functional state of CHIT1-expressing cells in MS remains a prerequisite. This is emphasized by the functional diversity and cellular heterogeneity of microglia and CNS-associated macrophages uncovered in recent work–.

In this work, we investigate five microglia/macrophage-related proteins – CHIT1, chitinase-3-like protein 1 (CHI3L1, also known as YKL-40), soluble triggering receptor expressed on myeloid cells 2 (sTREM2), glycoprotein non-metastatic melanoma protein B (GPNMB) and C-C motif chemokine ligand 18 (CCL18) in the CS

more disability progression over time. Our machine learning models showed that CHIT1 had the highest predictive power for faster disability progression, after established clinical prognostic factors such as baseline EDSS. The consistency of our results across methodologies emphasizes the robustness of CSF CHIT1 as a biomarker. Through the analysis of single-cell transcriptomic profiles from CSF as well as CNS tissue of MS patients, we found CHIT1 to be primarily expressed by a distinct microglia subset (MG4). These CHIT1+ cells were most abundant within active MS lesions. We discovered that the CHIT1+ cell state was enriched for pathways related to foam cell differentiation, lipid homeostasis and clearance, which suggests a role in the de- and/or remyelination processes in MS. Moreover, our pseudotime trajectory analysis illustrated that CHIT1 expression in microglia accompanies the transition from a homeostatic towards a more activated, MS-associated phenotype. Neuropathological evaluation of both early- and late-stage MS patients showed that CHIT1+ cells were indeed present in almost all actively demyelinating lesions, whereas completely absent in inactive lesions and normal-appearing white matter. CHIT1+ cells were consistently CD68+ and PLP+, confirming their involvement in phagocytosis of myelin degradation products.

CHIT1 has been investigated as a putative biomarker in several other neurological disorders,. The most extensive research has been conducted in amyotrophic lateral sclerosis (ALS), a prototypic neurodegenerative disease. In parallel to our results, CSF CHIT1 has repeatedly been shown to correlate with faster disease progression in ALS,. CHIT1 has also been implicated in lipid storage disorders such as Gaucher, Niemann-Pick and Fabry disease. Particularly in Gaucher disease, plasma CHIT1 has been commonly used in clinical practice for over a decade to monitor disease severity and effectiveness of treatment,. In these lysosomal disorders, CHIT1 was found to be a marker for specialized lipid-laden macrophages or foam cells,,. Interestingly, CHIT1 was suggested to reflect a particular activation or differentiation state of such lipid-laden macrophages rather than their absolute cell number. In accordance with these findings, our pathway and trajectory analyses as well as neuropathological evaluation implied that CHIT1 in MS also marks a subset of

NAWM (Fig. 7A). In active lesions however, small Iba1+ TMEM119+ cells with no or little uptake of proteolipid protein-positive (PLP+) degradation products were found to be CHIT1+ (Fig. 7B, C). Larger, foamy (PLP-laden) CHIT1+ cells were mostly TMEM119- and some also Iba1- (Fig. 7C–E). This was in line with our transcriptomic analyses where we found that AIF1 (the gene encoding for Iba1) was significantly downregulated in CHIT1+ cells as compared to CHIT1- cells (Supplementary Data 5) as well as along the pseudotime trajectories from homeostatic towards more activated, MS-associated microglia (Supplementary Data 6). Likewise, the loss of homeostatic microglia marker TMEM119 with the acquirement of CHIT1 expression corroborated our findings at the transcript level that CHIT1 expression in microglia accompanies the transition into a disease-/MS-associated phenotype. Interestingly, small CHIT1+ Iba1+ TMEM119+ cells (Fig. 7E) seemed to be present more towards the lesion edge, whereas larger, foamy CHIT1+ Iba1- TMEM119- cells were mostly found further away from the lesion edge (Fig. 7B, C). Double staining for CHIT1 and glial fibrillary acidic protein (GFAP) confirmed that none of the CHIT1+ cells were GFAP+ astrocytes (Fig. 7F). In addition, triple staining for CHIT1 together with Iba1 and CD68 illustrated that CHIT1+ Iba1- cells were still phagocytic CD68+ cells (Fig. 7G).

Discussion

We demonstrated that CHIT1 concentration in CSF at diagnosis is a robust predictor for faster disability progression in MS patients and reflects early microglial activation. In comparison to several other microglia/macrophage-related biomarkers, only CHIT1 was found to correlate with future disability in our single-time-point analysis. By means of multi-time-point EDSS assessments and mixed-effects models, we observed that MS patients with higher CSF CHIT1 concentrations at diagnosis experienced
```

</details>

## 20. `c81e899f`

**Question.** In the Alzheimer's subtype resembling the hippocampal-sparing variant, when does the hippocampus become abnormal relative to the other deep grey matter structures, and where is the loss concentrated?

**Reference answer.** The hippocampus starts becoming abnormal after most of the other deep gray matter structures, with loss predominantly focused in the insula, caudate nucleus and parietal cortex.

**Answer under review.**

> In the Alzheimer's subtype resembling the hippocampal-sparing variant, the hippocampus becomes abnormal after most of the other deep grey matter structures, with the loss predominantly focused in the insula, caudate nucleus, and parietal cortex.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
and GENetic Frontotemporal dementia Initiative (GENFI) or synthetic data, while in the present study we demonstrated model transferability to clinical cohorts through stable and consistent subtyping.

Subtype 1 mirrored the typical course of AD as supposed in heuristic models and as found in previous EBM and data-driven models, according to which hippocampus is one of the earliest regions to show considerable atrophy. This subtype also shares similarities with the typical subtype as defined in the original SuStaIn work for which hippocampus and amygdala are among the first regions to show atrophy. The correspondence of Subtype 1 with the canonical and most prevalent manifestation of AD, is reinforced by our subject subtyping results, with the majority of subjects assigned to this subtype in both training and test set. In particular, the proportions of AD subjects of the training and testing set assigned to Subtype 1, 79% and 95% respectively, are greater than those from other diagnostic categories. Subtype 1 is also majorly prevalent as assignment of pMCIs, with a proportion of 69% compared to the other diagnostic categories.

Subtype 2 shows similarities with the hippocampal-sparing variant of AD characterized by a relative sparing of the medial temporal lobe as observed in previous works. In this subtype hippocampus starts becoming abnormal after most of the others deep gray matter structures, with loss predominantly focused in the insula, caudate nucleus and parietal cortex. The similarity also extends to the demographic characteristics of this group, that is characterized by a higher prevalence of male subjects as reported in previous works. In this subtype, pallidum, putamen and caudate are among the first regions to show atrophy as observed in the subcortical subtype defined in the original SuStaIn work.

Subtype 3 is characterized by a broader atrophy signature with less distinct ordering than the other subtypes, with the exception of ventricles expansion that was clearly the first marker to become abnormal. In this atypical subtype, atrophy seems to progress simultaneously in most brain regions. Subtype 3 was observed in a minority of subjects when considering our whole cohort. These subjects exhibit similarities with the limbic predominant subtype of AD. Also, Subtype 3 might have some characteristics in common with other subtypes as some subjects had been labeled as belonging to the typical AD subtype. Alternatively, it is possible that this group does

version 3.5.1).

Chi-square and ANOVA tests (α = 0.05) were performed in python (version 3.6.9) to test differences between the diagnostic groups and subtypes.

Results

The disease model identified by SuStaIn consisted of three disease subtypes (Figure 1). The first disease subtype (“Subtype 1” in the next sections), is characterized by abnormality (Z-score = 1) that can be observed in the ventricles first, then atrophy occurs in the hippocampus and entorhinal cortex, that are also the first regions to show full abnormality (Z-score = 3) alongside amygdala. Interestingly, ventricles are also the last regions to show full abnormality meaning a relatively slow but persistent volumetric expansion process that tracks the disease progression.

The second disease subtype (“Subtype 2” in the next sections) shows an atrophy pattern where abnormality starts in thalamus and pallidum (Z-score = 1). Subsequently, atrophy can be observed in caudate, putamen, insula, precuneus and then fusiform gyrus and middle-temporal cortex and hippocampus which is the first biomarker to become fully abnormal (Z-score = 3). In this subtype, ventricles start expanding later than in Subtype 1. The third subtype (“Subtype 3” in the next sections) shows an atrophy pattern where ventricles become fully abnormal before atrophy starts in almost all the other regions, for which a less-defined atrophic progression is manifested in comparison to Subtypes 1 and 2.

SuStaIn subtypes were cross linked to AVRA ratings to evaluate whether similarities between subtypes defined by the two methods exist (Figure 2). Subtype 1 was mainly characterized by the “Typical AD” atrophy pattern; Subtype 2 showed an equal predominance of the hippocampal-sparing variant; Subtype 3 showed a limbic-predominant subtype. The minimal atrophy subtype was most consistent with Subtypes 1 and 2. After correcting against effects of sex, age and TIV, relevant differences (p-value for ANOVA <0.05) in volume of hippocampus were observed between subjects from Subtypes 1 and 2 labeled with minimal atrophy according

) and frontal gyrus and between the temporal and occipital gyrus. Additionally, a study showed that AD participants presented a larger caudate nucleus volume in AD, probably reflecting a compensation mechanism of damage in the closest areas such as the hippocampus. Pathology in the hippocampus could explain an increased stimulation of the caudate nucleus, causing an increase in volume and FC between it and the cortical brain regions.

On the other hand, the cerebellum was classically thought to be unaffected in MCI and AD. However, gray matter atrophy in the cerebellum and pathological changes, such as beta-amyloid deposits and neurofibrillary tangles, have been observed. The current results showed abnormal connectivity in the cerebellum and between the cerebellum and other regions (cerebellum crus II and DMN, sensory-motor and cerebellum VII, and cerebellum 8 and cerebellum 7b). Other studies also found aberrant FC within the cerebellum and between the Crus II and the DMN.

The precuneus, a specific region of the DMN, is a relevant hub that enhances connectivity between several brain regions. A decreased FC between this and other regions has been associated with changes in the brain’s vulnerability in early Alzheimer’s disease. Our PPA results showed a decreased FC in LMCI in contrast with HC. A decreased FC of the precuneus might be the cause of increased FC in regions next to this region (local hyperconnectivity hypothesis) and far from this region (global hyperconnectivity hypothesis).

The added value of SWA and the PPA to the static FC

Although our results showed some overlap or complementarity across methods, for instance, areas or networks, there were also differences across methods. It is worth noting that the PPA was able to detect more changes across groups.

Some areas that showed aberrant FC detected by means of the SWA and the PPA were not detected in the static FC. For instance, the AD presented less variability and more synchronicity between the auditory and middle frontal gyrus in comparison to the HC and the EMCI. In addition, the AD group, in contrast to the HC and the EMCI, presented increased FC and decreased variability between regions of the auditory network, e.g.,

On the other hand, early pathologic damage might explain the decreased FC in AD between the right middle temporal gyrus and the right superior occipital gyrus.

An increased FC has also been associated with mal(adaptive) rewiring of the brain after pathologic damage occurs. This idea is not mutually exclusive to the neurotransmitter dysregulation hypothesis, and the two mechanisms might co-occur in an additive fashion. Some authors have distinguished two types of hyperconnectivity rewiring after brain damage: local hyperconnectivity and global hyperconnectivity. The former states that local alternative paths close to damaged brain areas are used to ensure that communication between networks is possible to preserve function. The latter refers to the brain using multimodal or rich nodes, independently of the localization of the brain damage, in order to ensure the maintenance of cognitive function. Following the popular stages of AD degradation as proposed by research, the first areas damaged in AD (stages I and II) due to TAU deposition are the posterior ones, more specifically, the brain stem followed by the entorhinal. These areas are then followed by the limbic and whole neocortex in more advanced stages (III–IV), and then the hippocampus and anterodorsal thalamic nucleus. As the participants of our study present mild AD, this sign of increased FC in some posterior areas might indicate that certain regions of the posterior cortex could be affected but other areas are still preserved and can be recruited. A study showed increased correlations between occipital regions. Some investigators presented the same results regarding hyperactivity in AD in the middle occipital gyrus, lingual gyrus, and visual cortex and explained the findings as an adaptation of the brain networks in response to the disease.

Although several researchers have justified an increased FC in neurodegenerative diseases as an adaptive mechanism of neuroplasticity to protect behavior and cognition against brain damage, the mechanisms behind FC and its relationship with cognition and behavior are not well understood yet. Multiple factors play a role in FC, and at the time of writing, there is a lack of understanding of what is really causing a specific pattern of FC, i.e., what factors can explain an increased or decreased FC. Currently, interpretations of results in FC have been speculative. For instance, can an increase in FC in several areas be explained simply by structural disconnection
```

</details>

## 21. `133f02ae`

**Question.** What sensitivity and specificity did the time-latency classifier achieve for detecting mild cognitive impairment, and at what latency threshold?

**Reference answer.** At a 70 ms time-latency threshold it achieved 88% sensitivity and 87% specificity.

**Note from the gold set.** the source sentence is malformed -- 'The ROC achieved an AUC of 88% sensitivity and 87% specificity'; an AUC is not a sensitivity. The reference answer reads it as intended, and an answer reproducing the paper's own wording must not be penalised.

**Answer under review.**

> The provided context does not contain the answer.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
Table 5 presents the performance of each machine learning model in the testing sample. Accuracy, sensitivity, and specificity were identical across SVF and ensemble models. Nonetheless, the final ensemble model demonstrated the best overall performance (AUC = 0.93) compared to each individual ML model, with the speech-only model performing the worst (AUC = 0.64). For comparison, when differentiating impaired from non-impaired groups, the MMSE demonstrated an accuracy range of 71.1 to 80.7%, sensitivity range of 41.6 to 66.6%, and specificity range of 75 to 100% across cut-offs of 24 to 28, with an optimal cut-off of 27 yielding an accuracy of 76.9%, sensitivity of 66.6%, and specificity of 85.7%. When differentiating MCI from non-impaired, the MMSE demonstrated an accuracy range of 62.5 to 77.5%, sensitivity range of 8.3 to 33.3%, and specificity range of 75 to 100% across cut-offs of 24 to 28, with an optimal cut-off of 27 yielding an accuracy of 70%, sensitivity of 33.3%, and specificity of 85.7%.

[TABLE: Table 5]

Discussion

Novel automated technologies are emerging to allow methods to screen for subtle cognitive changes in older adults, as early detection is critical for diagnosis and initiation of appropriate care. This is especially important for historically marginalized racial and ethnic groups, who often experience delayed diagnosis of cognitive disorders and face barriers in accessing specialists for evaluation and treatment. Furthermore, these evolving technologies hold promise as brief, accessible, and scalable means of capturing emerging cognitive deficits. The current study explored the utility of an automated speech analysis algorithm to quickly and effectively screen for cognitive impairment in a Spanish speaking population.

Model performance

The current study provides support for the utility of a quick, 5-minute assessment that analyzes responses to language measures to investigate aspects of speech that may not be easily detectable to examiners. Early screening and detection of cognitive impairment in at-risk populations may allow for the proper allocation of time and resources to individuals identified as requiring more extensive assessment (e.g., biomarker analysis, comprehensive neuropsychological evaluation, neuroimaging, etc.). Additionally, this speech analysis tool may outperform current standard-of-care screening measures such as the Mini-Mental State Examination. In this study, the technology outperformed the MMSE in screening for MCI and dementia among Spanish speakers. The tool demonstrated superior accuracy (87.5/88.4), sensitivity (83.3%/87.5%), and specificity (89.2%/89.2%) when compared to an MMSE cut-off of 24 or 25, two thresholds well-established in clinical practice. While qualitatively different, the current model’s performance seems comparable, if not superior, to the MMSE.

Blesa and colleagues developed age and education-adjusted cut-off scores for the MMSE in a Spanish speaking cohort, identifying the optimal cut-off score to be 24/25 which yielded a sensitivity of 87.32% and specificity of 89.19% in detecting dementia. Similar results have been demonstrated using the Montreal Cognitive Assessment (MoCA) in the detection of MCI among Spanish speakers, with a sensitivity of 80.48% and specificity of 81.19%. Beyond its superior sensitivity, this technology fills a gap in the existing literature as a concise, cost-effective screening tool that is available through a web-based platform. The tool is fully automated, partially addressing issues related to the frequent incongruence between the patient and examiner’s native language, and ultimately emphasizing its ease and accessibility in primary care and community health settings. Furthermore, the impact of the current model is a promising avenue to increase cognitive screening, as it could be easily adapted to mobile phones, the feasibility and efficacy of which has been demonstrated in prior studies. Thus, the current technology may allow for screening of more individuals that may be otherwise unable to access care.

We then validated the DNN model as a binary classifier to detect the presence or absence of cognitive dysfunction using the MMSE threshold (a cut-off value of 23/24). The DNN model exhibited a high prediction accuracy for binary classification, with a sensitivity of 90% and specificity of 90%.

Variable Importance Vis-à-vis the Prediction of MMSE Scores

We evaluated the variable importance vis-à-vis the prediction of MMSE scores. Table 5 shows the variable importance in DNN prediction. Interestingly, the variable with the highest importance “age,” also showed the highest correlation coefficient in Spearman's rank-order correlation. In addition, albumin, Hb, and RBC exhibited high importance in DNN prediction.

[TABLE: Table 5]

Validation of Prediction Accuracy of DNN Model

In order to validate the prediction accuracy of the DNN model, we compared the predicted MMSE scores and ground truth MMSE scores in the Patient and Heathy groups. Figure 4 shows the scatter plots of the ground truth MMSE scores and those predicted by the DNN model. The predicted MMSE scores exhibited a significant positive correlation with the ground truth MMSE scores (r = 0.66, p < 0.001). The MAE was 3.43 with a standard deviation of 2.59.

Figure 5 compares the ground truth and predicted MMSE scores in the Inpatient and Heathy Groups. The ground truth MMSE scores (22.4 ± 5.4) in the Patient group were significantly lower than those in the healthy group (29.4 ± 1.3) (p < 0.05). The predicted MMSE scores (22.0 ± 3.9) in the Patient group were significantly lower than those in the Healthy group (27.6 ± 2.2) (p < 0.05), which was consistent with the relationship observed in the ground truth MMSE scores. There was no significant difference between the predicted (22.4 ± 5.4) and ground truth MMSE scores (22.4 ± 5.4) in the Patient group (p > 0.05). However, in the healthy group, the predicted MMSE scores (27.6 ± 2.2) were significantly lower than the ground truth scores (29.4 ± 1.3) (p < 0.05).

Introduction

Alzheimer’s disease (AD) is the most common form of dementia and constitutes a significant public health problem worldwide due to the increasing need of social and economic services for patients and their support systems. A particular clinical challenge in AD and related dementias is identifying the early stages of cognitive decline due to its insidious onset and progression. AD is characterized by neuropathological features that can occur 15 to 20 years prior to noticeable changes in cognition or daily function. Mild cognitive impairment (MCI) often represents a transitional stage between normal aging and dementia, and these individuals are at a greater risk of developing incident AD. Detecting early stages of cognitive decline is paramount for identifying those at greatest risk of progression to dementia and who may benefit from further evaluation and treatment. Improving the detection of early cognitive decline may lead to earlier initiation of disease modifying treatments to preserve independent functioning, which is crucial to a patient’s quality of life.

There currently exist numerous tools to help detect early clinical or pathological signs of MCI/dementia, including thorough clinical workups, neuropsychological evaluations, neuroimaging, and blood and cerebrospinal fluid biomarkers. While imaging and biomarker-based techniques can detect some neuropathological features associated with AD, some are invasive and not widely accessible for the purpose of early detection, and others are still in development. Formal neuropsychological evaluation is often an intrinsic part of the diagnostic process for detecting subtle changes in cognitive function in many centers. However, access to neuropsychological services may be limited due to various geographic, economic, and/or psychosocial factors, including limited access to healthcare resources, and therefore cannot be utilized effectively on a large scale. For these reasons, cognitive screening instruments are used as brief and cost-effective methods to identify individuals who require further evaluation and can be implemented across both primary care and specialized clinical settings. Primary care providers often serve as the first line of medical care for older adults concerned about their cognitive performance, yet physicians in primary care settings report feeling ill-equipped to recognize or document signs of cognitive decline, contributing to gross under-detection of MCI in primary care settings. Nonetheless, current screening methods are not sufficiently sensitive or reliable in identifying clinical signs in the very early stages of dementia, and more precise screening techniques that can capture subtle changes in cognition are needed to identify individuals who may benefit from further evaluation.
```

</details>

## 22. `a9865b23`

**Question.** What CSF tau threshold defined tau positivity in the linear mixed-effects models of vascular biomarkers?

**Reference answer.** Tau positivity was defined as a value above 24.8 pg/mL.

**Answer under review.**

> The provided context does not contain the answer.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
V measurements were recorded, and the mean value was used in statistical analyses.

Biomarker acquisition and analysis

Participants received a research lumbar puncture with standardized procedures, preanalytical preparation of CSF, and storage of CSF as previously described and in accordance with the recommended best practices. In brief, CSF (15–25 mL) was collected by routine lumbar puncture early in the morning after overnight fasting. Samples were processed, aliquoted into 500 μL fractions in polypropylene microtubes, snap-frozen, and stored at − 80 °C until assayed. Lumbar punctures were generally conducted within 1 year of the PWV measurements for the vast majority of the participants, although we included CSF data collected within 3 years of the baseline visit given research showing the stability of CSF biomarkers over several years.

CSF AD biomarkers examined were beta-amyloid (Aβ42), total tau (Tau), and the ratio of tau over beta-amyloid (tau/Aβ42). A small portion of cases (n = 18) had biomarkers analyzed in the facilities of ADx (Ghent, Belgium) using ELISA assays developed by ADx and commercialized by EUROIMMUN AG (Lubeck, Germany). The remaining cases’ samples (n = 106) were analyzed locally at UCSD using the automated Lumipulse platform using assays developed with established monoclonal antibodies (Fujirebio Inc.). Weighted Deming regression of a set of 113 CSF samples analyzed on both platforms demonstrated high correlation (Pearson’s R of.87 for Aβ42 and.95 for Tau), so the resulting equations were used to transform ADx values into native Lumipulse space for analyses. A cutpoint for biomarker positivity in Lumipulse space was derived from CSF samples from a larger cohort of 462 unique participants at the UCSD ADRC (ranging from cognitively normal to severely demented). The ratio of tau/Aβ42 was used as it appears to provide the best subdivision of individuals without dementia into those with and without pre-clinical AD. A 2-component mixture model was fit to the bimodal distribution of the log-transformed tau/Aβ42 ratio using the mixtools package version 1.2.0 for R, and the cutpoint of tau/Aβ42 > 0

Age increases the risk for mild cognitive impairment (MCI), or early dementia, which may impact memory and/or non-memory cognitive domains but typically spares functional abilities. MCI is linked to genetic vulnerability (APOE4), lifestyle and associated comorbidities (e.g., cardiovascular disease, traumatic brain injury, socioeconomic status (SES), education, obesity, depressive symptoms, etc.). Early Alzheimer’s disease accounts for approximately 50% of MCI incidence and is characterized by cognitive decline in memory domains (amnestic type); whereas, vascular dementia, the second most common subtype of dementia with an incidence of 14.5%, is characterized by deficits in non-memory cognitive domains (e.g. visuospatial skills, attention, language, etc.) without memory impairment (nonamnestic type,). A nongradual progression of cognitive deficits is consistent with neurodegenerative disease.

Biomarkers in early Alzheimer’s disease

In 2018, the National Institute on Aging and Alzheimer’s Association Research Framework, updated the definition and diagnostic process to identify Alzheimer’s disease (AD) using pathology markers documented in vivo or at postmortem examination. The advancement in biomarker diagnostic decision making moves away from a syndromal approach (i.e., symptoms and behavioral deficits) to a biological approach for staging AD and other neurological diseases. The understanding of beta amyloid (Aβ) and tau peptides as biomarkers in the CSF (Aβ42, Aβ40, t-tau, p-tau) in AD development has led to the AT(N) scoring system for neuroimaging assessment of AD and other neurological disease: A indicates PET ligand binding of Aβ plaques or low CSFAb42, T, CSF phosphorylated tau, N, neurodegeneration or injury (N). Current progress in detection of AD and other neurological disease depends on the presence of Aβ with or without tau or neurodegeneration in CNS and plasma biomarkers of disease, although p-tau plasma biomarker, NF1 and p-tau217 show promise in longitudinal studies for early AD. The preclinical phase based on biomarker positivity in CSF and PET, occurs prior to the onset of symptoms and is longer than the time of age proposed in MCI-AD. A

.52 was chosen as the value at which an individual was equally likely to belong to either component of the bimodal distribution. This cutpoint is highly consistent with a published cutpoint (tau/Aβ42 > 0.54) for AD biomarker positivity using the Lumipulse assays, derived against clinical read of amyloid PET scans and validated in multiple cohorts.

Statistical analysis

Demographics and clinical characteristics between those with and without CSF were compared by Student’s t-test and chi-squared tests as appropriate. Relationships between PWV and performance in each cognitive domain were analyzed with separate linear models adjusted for age, sex, education, and FSRP. These analyses were then repeated with APOE genotype or CSF AD biomarker status (+/-) added to explore the interaction of PWV and AD risk markers (APOE ε4+; tau/Aβ42+) on cognition (while adjusting for age, sex, education, and FSRP).

Additional post hoc analyses were performed to determine whether significant results were retained in models including the individual FSRP components in place of the overall FSRP. That is, in cases where there were significant results, we reran the primary analyses described above but in place of overall FSRP instead adjusted for systolic blood pressure, history of diabetes, cardiovascular disease and/or atrial fibrillation, current smoking, and use of antihypertensive medication. We also reran these analyses with the individual FSRP components listed above while adjusting for two more vascular risk factors: BMI and history of transient ischemic attack (TIA).

Results

Associations of PWV with participant characteristics

Across the cohort, there was a significant increase in PWV with increasing age in both men and women (p < 0.001), with no evidence of an interaction between sex and age (p =.89). Overall, men had higher PWV than women (p < 0.001) (Fig. 1A). There was no significant association between PWV and APOE ε4 status (Fig. 1B), nor between PWV and the level of CSF Tau or Aβ42, or the tau/Aβ42 ratio (Fig. 1C).

Associations of PWV with cognitive test performance

Performance on each of the cognitive domain scores is presented as a function of PWV in Fig. 2A. After adjusting

dementia versus MCI (n = 111) and CU (n = 30) individuals who did convert to AD dementia). For plasma Aβ42/Aβ40, the resulting cutoff was 0.066 pg/mL. For Plasma P-tau217, the resulting cutoff was 0.199 pg/mL. For plasma NfL, the resulting cutoff was 22.3 pg/mL. To note, binarized biomarker status was used for visualization purposes only to demonstrate theoretical differences in outcome trajectories.

Statistical analysis

Linear mixed-effects (LME) modeling was used to model longitudinal PACC, with five models tested in total: a basic model (age, sex, education), the basic model plus each of the three plasma biomarkers added separately (i.e., basic model + Aβ42/Aβ40; basic model + P-tau217; basic model + NfL), and the basic model plus all three plasma biomarkers together. LME models had random intercepts and random slopes with an unstructured covariance matrix. Normality of model residuals was confirmed to ensure appropariateness of LME modeling. Cox regression was used to model clinical conversion to AD dementia with the same models fit as above; all participants were right censored at last follow-up visit or at clinical conversion. A power analysis was performed in which the reduction in sample size needed to achieve 80% power to observe a 30% reduction in cognitive decline or clinical conversion was calculated in a scenario where each biomarker was used individually (based on univariate thresholds) or combined (based on a fitted multivariate model) to screen individuals for trial inclusion and in order to enrich the trial population for the relevant outcome. All biomarkers were treated as continuous variables after being log-transformed prior to any analysis.

The primary cognitive outcome was also analyzed using CSF biomarkers on the same subjects and results were compared between CSF and plasma models using the AIC. The larger the difference in AIC is between two models, the less plausible it is that the model with higher AIC provides the best fit–. The risk of AD dementia was not analyzed using CSF biomarkers because these biomarkers were consulted by neurologists during diagnosis, leading to potential circular reasoning.

Sensitivity analyses were also performed with (a) MMSE as the cognitive outcome instead of PACC, (b) all-cause
```

</details>

## 23. `4c203a9f`

**Question.** Did COL6A2 co-localize with the deposits in prion-protein cerebral amyloid angiopathy tissue, and where was it located instead?

**Reference answer.** COL6A2 did not generally co-localize with the deposits despite co-occurring in largely the same vessels; it localized more internally, as a component of the basal membrane.

**Answer under review.**

> COL6A2 did not generally co-localize with the deposits in prion-protein cerebral amyloid angiopathy (PrP-CAA) tissue but instead localized more internally as a component of the basal membrane.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
co-localized with the Prp deposits.

In the white matter no immunoreactivity was seen for Aβ or any of the marker proteins (Fig. 7p-t) in the control case. The CADASIL case showed characteristic pathology in the white matter, thickened vessel walls, in the white matter as is common with this condition. No Aβ pathology was present (Fig. 7u) Mild immunoreactivity for NDP was present and of the assessed proteins COL62A staining was most pronounced. APOE and APCS also displayed mild immunoreactivity related to the affected vessels (Fig. 7v-y).

In hypertension related small vessel disease the presence of COLA6A2 was most prominent while immunoreactivity for NDP, APOE and APCS was low but present (Fig. 7z-ad). Interestingly IHC analysis of the CARASAL cases showed only the prominent presence of COL6A2 in affected vessels while NDP, APOE and APCS were absent.

Taken our data together, from the tested panel of proteins, we recognize COL6A2 as a general small vessel disease marker. NDP, APOE and APCS are most prominent in CAA (type-1 and cotton wool) and Prp-CAA. Involvement of NDP, APOE and APCS in other small vessel diseases is varying from non (CARASAL) to mild (CADASIL). Importantly, NDP is explicitly suitable to evidently separate CAA from Aβ plaque pathology (Table 4).[TABLE: Table 4]

Discussion

One of the most prevalent cerebro-vascular diseases in the elderly is sporadic CAA, characterized by vascular deposition of amyloid-beta protein. CAA can occur as an isolated disease or as part of the pathology in AD. Several studies have indicated CAA as an important cause of cognitive decline. Currently, there is no treatment for CAA and its presence cannot be diagnosed pre-mortem. Therefore insight in the pathogenic mechanisms and the need for biomarkers are urgent. We performed an exploratory laser dissection-assisted LC-MS-MS analysis of AD brain tissue exhibiting severe CAA type-1 pathology, AD brain tissue without apparent involvement of CAA, and control brain tissue without AD related pathology. We show that the proteome of CAA type-1 is different from that of parenchymal plaque pathology in AD, which led to the identification of proteins selective

COL6A2, APCS and APOE in relation to other small vessel diseases we performed additional IHC on cases that present various types of vascular defects, i.e., cotton wool plaque pathology, prion CAA, cerebral autosomal dominant arteriopathy with subcortical infarcts and leukoencephalopathy (CADASIL), hypertension related small vessel disease and Cathepsin A-related arteriopathy with strokes and leukoencephalopathy (CARASAL). IHC was performed on sections that exhibited the relevant pathological characteristics of each disease including an additional CAA type 1 case. Immunoreactivity for Aβ, NDP, COL6A2, APOE and APCS was confirmed in the CAA type-1 case (Fig. 7a-e). Immunoreactivity for these proteins was also assessed and confirmed in case exhibiting hereditary cerebral haemorrhage with amyloidosis Dutch type (HCHWA-D), which is a heredity form of CAA-type-1 (Additional file 9: Figure S8).

In tissue with cotton wool plaques the pathology was confirmed using IHC for Aβ displaying pathology around capillaries and larger vessels with dyshoric changes extending deep into the parenchyma (Fig. 7f). Intense NDP immunoreactivity was observed related to capillaries and the dyshoric changes and to a lesser extend directly lining the larger vessels. COL6A2 showed intense immunoreactivity lining the capillaries and larger vessels (Fig. 7g). IHC for APOE and APCS presented a highly positive, staining that appeared similar to the Aβ staining.

The PrP-CAA tissue was confirmed negative for Aβ pathology (Fig. 7k) and showed positive for Prp (data not shown). NDP immunoreactivity was highly increased and localised to the affected vessels. NDP staining was more pronounced around affected capillaries than at affected larger vessels. COL6A2 immunoreactivity was clearly present around capillaries and larger affected vessels, of which the vascular pathology was clearly observed using haematoxylin. Although co-occurring in largely the same vessels COL6A2 did not generally co-localize with the deposits, but instead localized more internally as a component of the basal membrane. APOE and APCS were also highly present and

COL6A2 IHC showed some immunoreactivity in control and AD cases which was restricted to leptomeningeal vessels (Additional file 8: Figure S7) and a few large vessels in the brain tissue. In CAA type-1, immunoreactivity for COL6A2 was highly increased and includes brain capillaries and larger vessels. Immunoreactivity was mostly associated with the endothelium and/or the adventitia (Fig. 5g-i). Similar results were obtained using two different antibodies for COL6A2 (data not shown). HTRA1 IHC showed clear overlap with Aβ in both AD and CAA. Compact and diffuse staining was observed related to the vessels in the CAA cases and showed plaque pathology in the AD cases without CAA. Control cases were all negative for HTRA1 (Fig. 5j-l). IHC for APOE resulted in pronounced staining of the vasculature in CAA cases and appeared related to compact deposits as well as more diffuse dyshoric deposits. Also immunoreactivity of APOE was observed in the AD cases related to the Aβ plaques, although the staining was less intense than that related to the vascular amyloid in the CAA cases (Fig. 5p-r). APCS IHC illustrated the presence of this protein in relation with both diffuse and compact Aβ pathology in both the CAA and AD group. However, staining related to the plaque pathology was less intense than that related to the vascular Aβ pathology (Fig. 5m-o).

For quantification of the IHC, images were obtained at sites that, for the AD and CAA cases, had high Aβ pathological burden in nearby sections of the same tissue block. The percentage of positively stained pixels over a total of 5 images from each case was determined. Although this method is semi-quantitative, it allowed a region-specific analysis in line with the tissue obtained by laser capture dissection that was at the basis of the original mass spectrometry analysis. Using IHC quantification we observed strongly increased immunoreactivity in CAA type-1 cases for NDP and COL6A2, and moderate increases for APCS, HTRA1 and APOE, confirming the MS results (Fig. 6).

Specificity in relation to other small vessel diseases

To assess the specificity of Aβ, NDP,

the CAA type-1 group compared to the AD and control groups, to confirm our mass spectrometry results. Immunoblotting was performed on whole tissue lysates of the same cases as used for the mass spectrometry analysis. When comparing the CAA group with the control group we found significant differences in NDP expression (Fig. 4). For APOE, APCS and COL6A2, the data showed the same trend of increased abundance in the CAA group as the proteomics data, but the differences did not reach significance. A likely explanation for this is the higher variation of expression of these proteins in the tissue used for immunoblotting, which in contrast to the mass spectrometry exploratory analysis, was not selectively enriched for pathological burden using LCM, and instead included white matter, leptomeningeal vessels and grey matter with a lower pathological burden. To unequivocally demonstrate CAA related expression, we turned to IHC analysis of these same proteins, which, in contrast to immunoblotting, allows region specific analysis similar to the LCM-LC-MS-MS analysis. For this a separate cohort was used consisting of cognitively healthy control cases (n = 8) without any Aβ or tau pathology, 2) AD cases with severe Aβ plaque pathology but no vascular deposits (no CAA) (n = 8) and 3) AD cases with severe CAA type-1 pathology (n = 6).

First Aβ pathology was visualized and its presence was confirmed in AD and CAA type-1 cases showing plaques and vascular Aβ pathology, respectively (Fig. 5b and c). Then, IHC analysis was performed to gain information on the localization of the selected proteins. IHC for NDP showed pronounced immunoreactivity in CAA type-1 cases that appeared associated to the vasculature. NDP immunostaining in CAA, appeared to be associated with both compact Aβ depositions as well as more diffuse staining in the parenchyma in cases that exhibit dyshoric Aβ deposits. Staining was more pronounced related to capillaries compared to larger vessels. The AD cases with plaques were nearly devoid of immunoreactivity, controls did not show any immunoreactivity for NDP (Fig. 5d-f). Different antibodies against NDP showed similar results (data not shown).
```

</details>

## 24. `f256e59b`

**Question.** Which novel MHC-I partner does amyloid-beta-oligomer destabilisation of the synaptic MHC-I-beta2M complex impair the interaction with, and what reversed the resulting signalling impairment?

**Reference answer.** NCAM-1; inhibiting the amyloid-beta-induced destabilisation of the MHC-I complex with SCT reversed the neuronal signalling impairment.

**Answer under review.**

> The amyloid-beta-oligomer destabilisation of the synaptic MHC-I-beta2M complex impaired the interaction with NCAM1, and the stabilization of the MHC-I-beta2M complex by SCT reversed the resulting signalling impairment.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
SCT expression increased neurite density compared with HLA-A2.1-WT expression and GFP control when treated with Aβ, whereas HLA-A2.1-WT expression did not affect neuronal growth under the same conditions (Fig. 6A–C). These results suggested that the enhanced stability of the MHC-I-β2M complex ameliorated the Aβ-mediated downregulation of NCAM1 signaling in synaptic outgrowth.

Discussion

The present study revealed that Aβ oligomers destabilizes synaptic MHC-I-β2M complex, impairing the interaction with NCAM-1, a novel MHC-I partner. We here further showed that inhibiting the Aβ-induced destabilization of MHC-I complex by SCT can reverse the neuronal signaling impairment, harnessing a novel therapeutic strategy.

Although studies have been made about the role of neuronal MHC-I in synaptic plasticity, little was known about MHC-I function in neurological diseases. Especially, the connection between MHC-I function and its role in AD remained unclear, despite genetic analyses showing an increased frequency of some MHC-I alleles in individuals with AD. We here found that the unstable β2M-free MHC-I heavy chain was increased in AD brains (Fig. 2). The oligomeric Aβ was largely responsible for the destabilization of neuronal MHC-I-β2M complexes (Fig. 1). Aβ treatment caused MHC-I-β2M complex to degenerate into soluble β2M and β2M-free MHC-I heavy chain, leading to rapid internalization of MHC-I heavy chain followed by lysosomal degradation (Fig. 1). This β2M-free MHC-I heavy chain was also found to regulate synapse density negatively in glutamatergic neurons, which may be related with synapse loss in AD brains. MHC-I was also recently reported to be involved in the pathogenic mechanisms of the strongest risk factor of sporadic AD, apolipoprotein-E4.

Aβ oligomers induced extracellular release of β2M which was dissociated from surface MHC-I-β2M complex (Fig. 1E, H). Several proteomics analyses have identified

a novel interactor of MHC-I in human brain synaptosome.

Inhibition of NCAM1 expression and formation of NCAM1–MHC-I complexes in AD

Since NCAM1 is a novel interacting partner of neuronal MHC-I-β2M complex (Fig. 3) and MHC-I-β2M is destabilized by Aβ oligomers and in AD brains (Figs. 1, 2), we speculated that the interaction of NCAM1 with MHC-I-β2M complex is also deregulated. As expected, co-immunoprecipitation assay showed reduction in the amount of NCAM1-MHC-I-β2M complex in AD brains (Fig. 4A, B). In primary neurons, NCAM1 co-localized with MHC-I at the surface of the soma or dendrites, however Aβ oligomer reduced the co-localization intensity between MHC-I and NCAM1 or each protein levels (Fig. 4C–E). Aβ treatment reduced the amount of NCAM1 interacting with MHC-I by about 50% relative to control in primary neurons (Fig. 4F, G). Aβ treatment also reduced CREB phosphorylation, which is part of the final cascade of NCAM1 signaling (Fig. 4H, I), suggesting that the MHC-I–β2M complex is important for interacting with NCAM1 and activating its signaling. Together, these observations suggested that Aβ-mediated destabilization of MHC-I-β2M complex eventually impairs the formation of NCAM1-MHC-I-β2M complex, subsequently dysregulating NCAM1 signaling.

Stabilization of MHC-I-β2M complex rescued Aβ-mediated MHC-I depletion and dysregulation of NCAM1-MHC-I interactions

To determine whether inhibition of Aβ-mediated dissociation of MHC-I-β2M complex can rescue downregulated NCAM1 signaling through a recovery of interactions between MHC-I and NCAM1, we utilized a single-chain trimer (SCT) of MHC-I as an Aβ-resistant MHC-I-β2M complex. SCT, a synthetic gene encoding a sequential link of three

synaptic levels suggest MHC-I-NCAM1 interaction role in protecting NCAM1 decrease by Aβ oligomer (Fig. 5). NCAM, being a neuronal marker, is associated in AD. NCAM-deficient mice display reduced exploratory behavior and spatial learning, similar to the symptoms of AD in humans. NCAM levels are lower in frontal and temporal cortex AD patients than control patients and areare increased in serum of AD patients. Aβ mediates the shedding of NCAM2, another neural cell adhesion molecule, leading to loss of glutamatergic synapses. These results uggest that the overall stability of MHC-I is critical for its interaction with NCAM1 and potential role of MHC-I-NCAM1 interaction on pathogenesis of AD.

Various forms and alleles of MHC-I may regulate various synaptic functions via interactions with yet undetermined MHC-I receptors that can distinguish among MHC-I structures, suggesting the difference in regional or individual susceptibility of neurodegeneration in AD. The mechanisms regulating the transition of MHC-I structure and the identification of unidentified MHC-I interaction partners should be investigated further to understand the detailed functions of neuronal MHC-I.

Conclusion

In summary, we report a novel pathological mechanism of AD, the Aβ-mediated destabilization of the MHC-I-β2M complex and subsequent disruption of NCAM1 signaling. Furthermore, the SCT-mediated restoration of the MHC-I–β2M complex may be a promising therapeutic strategy for restoring synaptic function in AD patients.

Supplementary Information

Additional file 1: Figure S1. Analysis of expression of the peptide-loading complex components and glycosylation maturation of MHC-I in AD. A, B Immunoblot analyses of the components of the peptide-loading complex (ERp57, PDI, tapasin, and TAP) in aged normal and AD brains (A; n = 3 each). B The levels of ERp57, PDI, tapasin, and TAP were normalized to those of actin. C Intracellular MHC-I was immunoprecipitated from aged normal and AD brains, and digested with endoglycosidase-H (Endo-H) or peptide-n-glycosidase F

β2M as a potential biomarker in the CSF of patients with AD. Interestingly, β2M is a pro-aging factor that impairs cognitive function and neurogenesis, implying relations with AD. β2M could induce cognitive decline via neuroinflammation through toll-like receptor 4 (TLR4). Hence, the increased release of β2M downstream from Aβ-induced dissociation of MHC-I-β2M complex (Fig. 1) could be related with neuroinflammation and neurodegeneration in AD. How Aβ oligomer dissociates MHC-I-β2M complex is yet uncertain. Aβ oligomer might dissociate MHC-I complex directly or indirectly via unknown mechanisms. Leukocyte immunoglobulin like receptor B2 (LilrB2) is a well-known binding partner with MHC-I. Aβ oligomers bind to LilrB2, which might be a way of dissociating MHC-I-β2M complex indirectly. LilrB2 has a binding preference to β2M-free MHC-I heavy chains rather than the MHC-I-β2M complex in vitro. Additional studies are required to assess the detailed mechanism of MHC-I dissociation and toxic effects of Aβ-mediated extracellular β2M.

Because the function of MHC-I is mainly dependent on the protein with which it interacts, the identification of these proteins interacting with neuronal MHC-I is important for understanding MHC-I function in the CNS. We found here that NCAM1 protein is a novel functional receptor of MHC-I in the CNS (Fig. 3). NCAM1 is expressed in the adult CNS, is highly conserved in vertebrates, and is important for neurite outgrowth and synaptic plasticity in the hippocampus. Aβ decreased the interaction of NCAM1 with MHC-I, and NCAM1 downstream signaling (Fig. 4). Further investigation on the mechanism of NCAM decrease induced by Aβ oligomers is required to elucidate role of MHC-I in NCAM stability. While independent effect of Aβ oligomer on NCAM decrease is also possible, SCT-mediated MHC-I stabilization rescue of decreased NCAM levels and restoring
```

</details>

## 25. `86b9a351`

**Question.** In rats transgenic for human mutant tau, how did microglial numbers at 10 months compare with controls, and what had changed by 18-20 months?

**Reference answer.** At 10 months there were no differences in microglial numbers between transgenic and control rats; by 18-20 months the microglia showed extensive proliferation and an activated phenotype.

**Answer under review.**

> At 10 months of age, the number of microglia in R962-hTau rats was comparable to that seen in control animals. In contrast, dramatic increases in the number of microglia were observed in the subiculum (p =.0002), CA1 (Fig. 5A; p <.0001) and the hilus of the dentate gyrus (p <.0001) in 18–20-month-old transgenic rats.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
NS)]. To confirm the histological observations of ventricular dilation and brain atrophy, we performed an MRI analysis of an individual rat at 15 months of age (Fig. 4C), which confirmed in vivo these prominent anatomical alterations akin to overall consequences of tauopathy in the human.

Given the alterations in brain structure, we counted the number of NeuN-immunoreactive nuclei in the hippocampus (Fig. 4D, E). No differences were observed in the 10-month-old cohort in layers CA1 and CA2. However, in transgenic rats aged 18–20-months, we observed an extensive loss of neurons throughout CA1 (p <.0001) and CA2 (p <.0001) (Fig. 4E).

Activation of microglia and astrocytes in regions with tau pathology

3.5

We investigated whether alterations in glial cell numbers and morphology occurred in R962-hTau rats. We used antibodies against microglial/macrophage ionized calcium-binding adapter molecule 1 (Iba1), and the astrocyte-specific protein, glial fibrillary acidic protein (GFAP).

At 10 months of age, the number of microglia in R962-hTau rats was comparable to that seen in control animals. In contrast, dramatic increases in the number of microglia in the subiculum (p =.0002), CA1 (Fig. 5A; p <.0001) and the hilus of the dentate gyrus (p <.0001) were observed in 18–20-month-old transgenic rats (Fig. 5C).

Some microglial cells were seen to localise around AT8-immunopositive neurons (Fig. 5A, centre panel inset), however, there were no differences in microglial numbers at 10 months of age between transgenic and controls rats (Fig. 5B). At later time points (18–20-months), along with extensive proliferation (Fig. 5C), microglia displayed an activated phenotype (Fig. 5D). Additionally, some microglia adopted a distinct, rod-like phenotype, which has previously been described in AD patients and in experimental models of traumatic brain injury. Rod-like microglia ran parallel, either individually or in trains (Fig. 5E

of the first rat line transgenic for full-length human tau with the P301S mutation. We demonstrate the progressive, age-dependent increase in the accumulation of filamentous tau, which was upstream of neurodegeneration, myelin abnormalities, gliosis and behavioural deficits. In contrast to the transgenic mouse model where human P301S tau forms filamentous aggregates, aggregates of the R962-hTau rats comprised both human transgenic tau as well as endogenous rat tau in older timepoints.

Rat models of tauopathy have been generated. Notably, the first report of transgenic rat lines expressing human truncated tau demonstrated the brain occurrence of sarkosyl extracted tau fibrillary material consisting of both endogenous and human tau. Furthermore, these truncated models described the presence of inclusions within the spinal cord and brainstem, resulting in motor and coordination deficits early and independently of neuronal loss. In these models, no neuron loss was detected in the hippocampus or cortex. A rat model of CNS tauopathy resulting from the transgenic expression of the full-length human tau with the FTDP-17T-associated P301L mutation, was reported by Korhonen and collaborators. This model, however, displayed minor tau pathology, and an absence of neuronal loss and behavioural impairment. This difference is likely attributable to a weak transgene expression; the authors reported around 30% of their transgenic rats failed to produce detectable levels of either human tau protein or mRNA even though they utilised a mouse prion protein (mPrP) promoter, which usually enables a high transgene expression. Furthermore, the mPrP promoter drives transgene expression to regions differing from those where the CamKIIα promoter is active, for example in the spinal cord. The P301L and P301S are both missense mutations located within exon 10 and are associated with FTDP-17. These mutations both strongly reduce microtubule assembly, albeit a smaller effect is observed with P301S compared to P301L.

Tau transgenic mice have been more frequently used and recapitulate, to varying extents, important disease features. Among the most commonly used models are those with the P301S and P301L mutations, including 0N4R P301S, PS19 and Tg4510 models which

(HT7), since no change in the expression of endogenous rodent tau (T49) was observed (Supplementary Fig. 2B).

Pathological changes in human and endogenous tau occur with age

3.2

We investigated the extent and distribution of tau neuropathology present in the R962-hTau rat model between 3 and 20 months of age (Fig. 1). Using antibodies directed against human tau, endogenous rodent tau, and different tau posttranslational modifications, we observed age-dependent alterations in the tau immunoreactivity, reminiscent of the human tauopathies. As predicted by promoter activity and expression, HT7 immunoreactivity was present throughout the forebrain, but absent in control rats (Fig. 1A). An age-dependent increase in human-specific tau immunoreactivity (HT7) was observed to be strongest initially in the hippocampus (Fig. 1B) as well as the somatosensory, entorhinal and piriform cortices (Supplementary Fig. 3). Immunoreactivity was most prominent within cell somas and axons at 3–6-months of age, and appeared more dendritic in nature at later time points, localizing to the neuropil (Fig. 1B). Some immunoreactivity was observed in spinal cord and inferior colliculus, two regions where the CaMKIIα promoter is reportedly not expressed; however, immunoreactivity there was minimal, and no NFT-like inclusions were observed.

Rat tau (T49) became involved in the pathology only relatively late; endogenous aggregated tau was occasionally observed at 6- and 10-months. However, the consistent sequestration of rat tau was not observed until 18–20-months (Supplementary Fig. 4). Rat tau was particularly abundant in inclusions in layers II-III and V of the somatosensory cortex and in hippocampal neurons (Fig. 1B).

At early pathology stages, hyperphosphorylated and conformationally-altered tau immunoreactivity was observed throughout hippocampal formation and cortical regions (Fig. 1C). Phosphorylation-dependent immunoreactivity was largely localized to the fascioloa cinerea, subiculum and granular cell layer of
```

</details>

## 26. `56d5ae49`

**Question.** In rats transgenic for human mutant tau, how did microglial numbers at 10 months compare with controls, and what had changed by 18-20 months?

**Reference answer.** At 10 months there were no differences in microglial numbers between transgenic and control rats; by 18-20 months the microglia showed extensive proliferation and an activated phenotype.

**Answer under review.**

> At 10 months of age, the number of microglia in R962-hTau rats was comparable to that seen in control animals. By 18–20 months, there were dramatic increases in the number of microglia in the subiculum, CA1, and the hilus of the dentate gyrus compared to both controls and younger transgenic rats.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
At 10 months of age, the number of microglia in R962-hTau rats was comparable to that seen in control animals. In contrast, dramatic increases in the number of microglia in the subiculum (p =.0002), CA1 (Fig. 5A; p <.0001) and the hilus of the dentate gyrus (p <.0001) were observed in 18–20-month-old transgenic rats (Fig. 5C).

Some microglial cells were seen to localise around AT8-immunopositive neurons (Fig. 5A, centre panel inset), however, there were no differences in microglial numbers at 10 months of age between transgenic and controls rats (Fig. 5B). At later time points (18–20-months), along with extensive proliferation (Fig. 5C), microglia displayed an activated phenotype (Fig. 5D). Additionally, some microglia adopted a distinct, rod-like phenotype, which has previously been described in AD patients and in experimental models of traumatic brain injury. Rod-like microglia ran parallel, either individually or in trains (Fig. 5E), to neuronal projections from the fascioloa cinerea, subiculum, CA1 and layers III and V of the primary somatosensory and entorhinal cortices respectively.

Alterations in astrocytic GFAP expression were also quantified at 10 and at 18–20 months of age. No differences were observed at 10 months when compared with age-matched controls (Fig. 5F, G). However, increases in GFAP total fluorescence and fluorescence area was observed in CA1 and the molecular layer of the dentate gyrus at 18–20-months (Fig. 5F, H).

Extensive myelin degeneration occurs in aged R962-hTau rats

3.6

To determine if a loss of white matter was associated with the degeneration in grey matter, we stained tissue sections with Luxol Fast Blue. This revealed demyelination in the corpus callosum of transgenic rats when compared with control animals at 18–20-months, indicating this pathology occurs secondary to upstream tau aggregation (Fig. 5I).

In order to characterise alterations in brain volume and structure, we performed morphometric analysis of coronal brain sections (Fig. 4A, Supplementary Fig. 8B). By 18–20-months of age, we found an increase in ventricle size (p =.001), a decrease in brain volume in the frontal cortex (p =.001) and hippocampus (p =.0057) (Fig. 4B). Brain atrophy and ventricular dilation were not observed in R962-hTau rats at the 10-month time point, despite progressive tau pathology (Fig. 4A). No interaction between sex and genotype for ventricle volume was observed [Genotype:Sex interaction, p =.48, not significant (NS)]. To confirm the histological observations of ventricular dilation and brain atrophy, we performed an MRI analysis of an individual rat at 15 months of age (Fig. 4C), which confirmed in vivo these prominent anatomical alterations akin to overall consequences of tauopathy in the human.

Given the alterations in brain structure, we counted the number of NeuN-immunoreactive nuclei in the hippocampus (Fig. 4D, E). No differences were observed in the 10-month-old cohort in layers CA1 and CA2. However, in transgenic rats aged 18–20-months, we observed an extensive loss of neurons throughout CA1 (p <.0001) and CA2 (p <.0001) (Fig. 4E).

Activation of microglia and astrocytes in regions with tau pathology

3.5

We investigated whether alterations in glial cell numbers and morphology occurred in R962-hTau rats. We used antibodies against microglial/macrophage ionized calcium-binding adapter molecule 1 (Iba1), and the astrocyte-specific protein, glial fibrillary acidic protein (GFAP).

To test visual-spatial memory, we employed the Morris water maze test. While 10-month-old transgenic rats performed similarly to controls (Fig. 7E), at 18–20 months of age, there was a significant Genotype:Training day interaction (p =.034) and significant main effects for both genotype (p =.032) and training day (p <.0001). The failure of R962-hTau to learn the task by day 5 supports this (Day 5; p =.008). Representative images of searching patterns during day 5 illustrates directed-searching for both genotypes at 10-months of age, and in 18–20-month-old controls, but random-searching in 18–20-month-old R962-hTau rats (Fig. 7E, F). These results are consistent with severe impairments in memory and learning. During the probe trial, the platform was removed, and latency to reach the platform zone and entries into the platform zone recorded. The probe trial followed a similar trend with a tendency for WT rats to have lower latency times to the platform area and higher number of entries into the platform zone, however, these failed to reach significance (Supplementary Figs. 9F and 10A, B). This is probably due to insufficient power or the intrinsic phenotypic variations. A factor perhaps not as relevant across training days due to training repeats. During the visible platform trial, all rats reached the platform, thus no rats were excluded on the basis of sensorimotor deficits or lack of motivation.

Fear conditioning

3.8.3

Immunoreactivity with phosphorylation-dependent anti-tau antibodies appeared to precede that with MC1. However, we observed variability between immunoreactivity for different tau antibodies and cellular localisation of tau at the same age (Supplementary Fig. 7B), a factor that was not dependent on sex.

Numerous inclusions were identified by modified Bielschowsky silver, throughout the cortex and hippocampus of R962-hTau rats (Fig. 2B, left and middle right panels). Axonal spheroids were also stained (Supplementary Fig. 7A). In control rats, only nerve cell axons were silver-positive.

Biochemical analysis reveals age-dependent accumulation of endogenous and human insoluble tau

3.3

Using a panel of anti-tau antibodies, sarkosyl-insoluble fractions from 10- and 18–20-month-old R962-hTau rats were analysed by Western blot. To ascertain how this compares to transgenic mouse models of tauopathy, samples were run alongside those from end-stage mice expressing the 0N4R human Tau with the P301S mutation under the control of the murine Thy1 promoter.

Sarkosyl-insoluble fractions from control rats and mice did not exhibit any insoluble tau material. At 10 months of age, human aggregated tau was detected in cortex and, to a lesser extent, hippocampus of R962-hTau animals (Supplementary Fig. 8A), similar to the aggregation patterns observed by immunohistochemistry. This tau ‘load’ was greater in the old R962-hTau rats and comparable to that seen in P301S mice (Fig. 3A). Unlike the P301S mouse model where rodent tau was undetected, endogenous rat tau was present in the sarkosyl-insoluble fractions of 18–20-month-old R962-hTau animals (Fig. 3B).
```

</details>

## 27. `8e25d463`

**Question.** Which pathway was found to be co-expressed with both the Alzheimer's and Parkinson's disease pathways despite having no significant gene overlap with them?

**Reference answer.** The proteasome pathway, which is co-expressed with both the AD and PD pathways yet has no significant gene overlap.

**Answer under review.**

> The proteasome pathway was found to be co-expressed with both the Alzheimer's and Parkinson's disease pathways despite having no significant gene overlap with them.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
The top AD-associated pathways are functionally related. We examined the 30 most highly studied KEGG pathways in terms of their gene overlap and co-expression to determine the degree to which pathways that are functionally interrelated are being mentioned for their roles in AD. The neurodegenerative disease pathways, namely, Huntington’s disease, Parkinson’s disease, and Alzheimer’s disease all have genes in common and are co-expressed (Figure 6A). Even when gene overlap is controlled for, they still co-express, suggesting they are functionally interconnected. In contrast, Parkinson’s and Huntington’s disease pathways are not enriched in the predetermined set of known AD-associated genes. We observed that several pathways are clearly functionally related while not being significantly enriched within each other. These results suggest functional interconnectivity of AD-associated pathways beyond gene-sharing mechanisms and warrant further exploration. For example, the neurodegenerative disease pathways are highly co-expressed with the proteasome pathway, which describes a protein-degradation complex, potentially linking in protein misfolding with these disorders. Even when gene overlap is controlled for, they still co-express, suggesting they are functionally interconnected. Each of these is also highly co-expressed with the proteasome pathway, which describes a protein-degradation complex, potentially linking protein misfolding with these disorders. In contrast, Parkinson’s and Huntington’s disease pathways are not enriched in the predetermined set of known AD-associated genes.

We examined pathway co-expression to compare the organization of the top 30 ranked KEGG pathways with those that show gene overlap in a network (Figure 6B). The network contained 89 pairs of pathways with a significant correlation (FDR < 0.05). This network contains several links that are not captured in the enrichment-overlap network (Figure 6A). For example, we found that the proteasome pathway is co-expressed with both the AD and PD pathways, yet it has no significant gene overlap.

Discussion

We have investigated the pathway-specific literature surrounding dementia with a focus on AD by text-mining abstracts with a number of curated dictionaries. The majority of pathways can be associated with AD. Counting only five studies as sufficient support, a total of 91% of KEGG pathways could be related to AD. This number decreases to 88% (10 studies), 63% (50 studies), and still 49% with greater than 100 studies (Supplementary Table 4). Nevertheless, even these low-association pathways have abstracts, which state a manually verified association, for example, the ferroptosis pathway only has 13 studies to link it to AD, yet 10 of these score highly as a true association (Supplementary Table 4). On the other end of the pathway rankings, the PD pathway has the second highest number of publications after AD (Figure 2), due to both diseases often being mentioned together as related even if the study is analyzing only one disease. If we only include studies with an adequate AD word association score, the top ranked pathways after AD are immune system, metabolic pathways, cholinergic synapse, long-term depression and then apoptosis, while Parkinson’s disease still ranks high at the fifteenth place (Supplementary Table 4). Alzheimer’s disease is not the only disease in which a large number of pathways have been implicated, but cancer has also been ubiquitously associated across genes and pathways.

To determine co-expression patterns among AD-associated pathways, we used the Pathway Co-expression Network (PCxN) customized to KEGG-only pathways. PCxN generates a canonical co-expression network among a given set of pathways using 3,207 gene expression profiles from 72 tissues. In PCxN, each edge represents a partial correlation between gene expression summary statistics of two pathways. Each summary statistic in PCxN is a proxy value of a pathway’s expression calculated from its member genes. The partial correlation between the two pathways is conditioned on, and corrected for, the overlap between them. We extracted the co-expression network of the top 30 literature-associated KEGG pathways. The network was processed and visualized using the R-igraph package. Only those PCxN-edges with statistically significant correlation (FDR < 0.05) were included in the network construction. The edge thickness is proportional to the absolute value of correlation coefficient between two nodes. The correlation network was mapped to the layout from the network of the pathway overlap analysis for comparability. Given the slight differences in the background of the text-mining pathways and those annotated in PCxN, only pathways present in both datasets were included for visualization.

Results

Pathway Associations

We found that 325 of 335 KEGG pathways and all 6 additional pathways (immune system, cancer, diabetes, adaptive immune system, innate immune system, and cytokine signaling in immune system) have publications containing an association with AD. Of the unrelated KEGG pathways, two could be connected to dementia in general. Pathways with the strongest literature association to dementia were Alzheimer’s disease, Parkinson’s disease, immune system (added to our KEGG list), metabolic pathways, long-term depression, cholinergic synapse, diabetes (also added), and apoptosis. If we restrict this to AD-specific studies only, we get similar, most frequent literature association pathways, namely, Alzheimer’s disease, immune system, metabolic pathways, cholinergic synapse, long-term depression, apoptosis, proteasome, diabetes, cancer, and chemokine signaling pathway (Supplementary Table 4). The 7 pathways not related to AD or dementia were amino sugar and nucleotide sugar metabolism, amoebiasis, antifolate resistance, collecting duct acid secretion, maturity onset diabetes of the young, proximal tubule bicarbonate reclamation, and yersinia infection.

We questioned to what degree AD-associated pathways in the literature exhibit overlap and share genes using enrichment analysis. The 30 most frequently published AD-associated pathways include several significant overlaps. For example, Alzheimer’s disease (171 genes) and Parkinson’s disease (142 genes) pathways share more than 94 genes (p-value < 10E-134). A gene overlap network displays one large component that includes most of the top 30 pathways (Figure 6A). The network contains 199 pairs of pathways with a significant overlap (FDR < 0.05), showing significant gene sharing among the most frequent AD-associated pathways.

In contrast, analysis of KEGG pathways with a set of AD-associated genes from the Open Targets disease gene prioritization system shows enrichment in 8 of the top 30 pathways (FDR < 0.05), including Parkinson’s disease and Huntington’s disease pathways. We found that pathways that demonstrate enrichment have a higher literature ranking compared with the pathways that are not enriched (p-value = 0.0136, Wilcoxon’s rank-sum test; Supplementary Table 8). Surprisingly, the most significantly enriched pathways are not the most highly ranked and include nicotine addiction, followed by neuroactive ligand-receptor interaction, cocaine addiction, morphine addiction, retrograde endocannabinoid signaling, GABAergic synapse, amphetamine addiction, taste transduction, and cAMP signaling pathway. However, after these nine pathways, seven highly ranked pathways also show enrichment in the following order: Alzheimer’s disease, serotonergic synapse, calcium signaling pathway, dopAMinergic synapse, alcoholism, ALS, and glutamatergic synapse.

Using a genetically defined AD gene list, many more immune pathways were enriched, including, in the following order of significance: asthma, hematopoietic cell lineage, allograft rejection, graft-versus-host disease, type I diabetes mellitus, antigen processing and presentation, leishmaniasis, intestinal immune network for IgA production, autoimmune thyroid disease, viral myocarditis, and inflammatory bowel disease (Supplementary Table 9).

Pathway Co-expression
```

</details>

## 28. `00585606`

**Question.** Which astrocytic structures wrap the neurons containing cisplatin-induced tau deposits, and which endothelial marker also associated with some deposits?

**Reference answer.** AQP4-positive astrocyte endfeet wrap those neurons, and some tau deposits also associated with CD31-positive endothelial cells.

**Answer under review.**

> The neuron-facing membrane domains of astrocytes, as indicated by AQP4 staining, wrap the neurons containing cisplatin-induced tau deposits. Some tau deposits also associate with CD31+ endothelial cells.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
closely associated with GFAP+ filaments (Fig. 3C and D) or the perinuclear region of GFAP+ cells indicating the presence of tau deposits intracellularly in astrocytes (Fig. 3D).

Most of the tau deposits in the hippocampus (Fig. 4A-G) and entorhinal cortex (Fig. 4H) colocalized with MAP2, indicating that they are inside neurons. Indeed, high magnification images reveal wrapping of the deposits by MAP2+ microtubules (Fig. 4B-C and E-G). We used aquaporin-4 (AQP4) staining to evaluate the association of tau aggregates with astrocyte endfeet. We observed two patterns of AQP4 staining – channel-like tubular structures representing the perivascular endfeet of astrocytes (p-AQP4) (Fig. 4D, H and 5A-D) and disc-like granular structures indicative of the neuron-facing membrane domains (n-AQP4) of astrocytes (Figs. 4B-C, E-H and 5A-D).

Figure 5

The tau deposits distinctly appeared at the granular, neuron-facing membrane domains of the astrocytes (Figs. 4B-C, E-H and 5A-D). Three-dimensional (3D) orthogonal slice and volume views reveal that the neurons containing tau deposits (as indicated by the colocalization with MAP2) are wrapped by AQP4+ astrocyte endfeet (Fig. 4C, F-G). Some tau deposits also associated with CD31+ endothelial cells. (Fig. 6A and B). Interestingly, meningeal cells lining the brain also contained intracellular aggregates of tau (Fig. 7A and B).

No signs of neuroinflammatory activity or senescence in the brains of cisplatin-treated older mice

We described previously that cognitive impairment in young (8–10-week-old) male and female mice treated with cisplatin was not associated with signs of neuroinflammation as assessed by real-time PCR or RNAseq analysis of hippocampal samples obtained during or at various time points after treatment. In view of the reported increase in neuroinflammation during aging and the localized astro

the cisplatin-induced cognitive deficits. Most importantly, delayed treatment with MSC at one month after the last dose of cisplatin normalized behavior in the PBT and the NOPRT in both sexes.

Discussion

The long-term sequelae of cancer and its treatment include signs of accelerated aging that affect a growing population of cancer survivors. Cognitive decline, a sign of brain aging, is amongst the most devastating of these adverse consequences. Increasing evidence indicates that chemotherapy for cancers outside the nervous system increases the risk of cognitive impairment. Nevertheless, multiple epidemiologic studies have shown that there is an inverse relation between cancer and Alzheimer disease [–]. Although this seems counterintuitive, cognitive decline associated with accelerated aging may well be independent of the development of Alzheimer disease. Indeed, a study in patients treated for colorectal cancer showed that chemotherapy increased the risk of cognitive decline, while in the same cohort the risk of developing Alzheimer disease was reduced.

Here, we investigated the effect of the chemotherapeutic cisplatin on two signs of accelerated aging; cognitive decline and the formation of tau deposits in the brain. We show that treatment of 9-month-old mature adult male and female mice with cisplatin accelerates the formation of tau deposits in the brain, a hallmark of brain aging. The tau deposits in the brain of cisplatin-treated mice are restricted to the hippocampus and entorhinal cortex. Deposits of tau colocalized with syndecan-2 and were mainly found inside neurons that were surrounded by the aquaporin 4 positive neuron-facing membrane domains of astrocytes. In search for an intervention, we demonstrate that nasal administration of bone marrow derived MSC at 48 and 96 hours after completion of chemotherapy prevented tau cluster formation and normalized cognitive function in male and female mice. Importantly, nasal MSC administration also prevented tau cluster formation and cognitive deficits when treatment was delayed until one month after completion of cisplatin treatment.

In humans, accumulation of tau deposits is thought to be part of normal brain aging and is strongly linked to age-related cognitive decline [, –]. These tau depositions are first developing in the entorhinal cortex and spread to the hippocampus and other brain areas later in life. Mice also develop tau deposits in the hippocampus during healthy aging and these deposits are first detectable at an age of 12–14 months. Consistently, we detected sparse tau deposits in the hippocampus of control mice

Iba-1 staining either directly after cisplatin treatment or at different time points after completion of dosing, we did not detect signs of inflammation between control and cisplatin treated mice. These findings contrast with the increased Iba1 staining and brain pro-inflammatory cytokine production in mouse models of Alzheimer disease. It should be noted, however, that the tau pathology in those models is caused by overexpression of human proteins and includes increases in hyperphosphorylated tau as identified using the AT8 antibody.

In conclusion, we show that cisplatin accelerates formation of tau deposits in the hippocampus and entorhinal cortex of older male and female mice. Moreover, we show that nasal administration of MSC up to 1 month after completion of cisplatin treatment prevents this sign of accelerated aging and the associated cognitive deficits.

Materials and methods

Animals

Female and male C57BL/6 J mice (Jackson Laboratory) of 9 months of age at start of the study were housed at a temperature of 22 ± 2 °C and 12/12 h reverse dark-light cycle (dark 830–2030 h) with food and water ad lib. Mice were randomly assigned to treatment groups.

Chemotherapy

Mice were treated with cisplatin in 2 rounds of 5 daily intraperitoneal (i.p.) doses of 2.3 mg/kg in phosphate-buffered saline (PBS) with 5 days of rest in between or with vehicle (PBS).

MSC

Human MSC were cultured in Minimal Eagle Essential Medium (Corning Life Sciences, Corning, NY, USA) supplemented with GlutaMAX™ (ThermoFisher Scientific, Gibco, Life Technologies Corporation, Grand Island, NY, USA), 2 USP units/mL heparin (Fresenius Kabi USA, Lake Zurich, IL), 7.5% heat inactivated Fetal Bovine Serum (FBS, Sigma-Aldrich, St. Louis, MO, USA), 2.5% platelet lysate (PLTMax®, Mill Creek Life Sciences, Rochester, MN, USA) and 100 units/ml penicillin-streptomycin (Sigma-Aldrich, St. Louis, MO, USA) as described. The cells were positive for CD29, CD44, CD73, CD90, CD105, and CD166. The MSC were and negative for CD14, CD19, CD34,
```

</details>

## 29. `c4ee8217`

**Question.** In rats transgenic for human mutant tau, how did microglial numbers at 10 months compare with controls, and what had changed by 18-20 months?

**Reference answer.** At 10 months there were no differences in microglial numbers between transgenic and control rats; by 18-20 months the microglia showed extensive proliferation and an activated phenotype.

**Answer under review.**

> At 10 months of age, the number of microglia in R962-hTau rats was comparable to that seen in control animals. In contrast, dramatic increases in the number of microglia in the subiculum (p =.0002), CA1 (Fig. 5A; p <.0001) and the hilus of the dentate gyrus (p <.0001) were observed in 18–20-month-old transgenic rats (Fig. 5C).

<details><summary>Retrieved passages (what the system was shown)</summary>

```
In summary, this study supports the idea that rats transgenic for full-length human mutant tau are promising models, particularly, for studying the spatio-temporal progression of tau pathogenesis and how it relates to neurodegeneration. In this regard, this model has shown that tau aggregation lies upstream, followed by the sequestration of endogenous tau, microglia proliferation, reactive astrocytes, myelin abnormalities, neuronal loss, ventricular dilation, brain atrophy, concurrent with development of memory and learning deficits. It highlights that rat brains show resilience to the initial tau pathology and that marked cognitive impairments are coincidental with advanced tau pathology and neurodegeneration, a situation resembling the evolution and clinical presentation of AD and other tauopathies.

At 10 months of age, the number of microglia in R962-hTau rats was comparable to that seen in control animals. In contrast, dramatic increases in the number of microglia in the subiculum (p =.0002), CA1 (Fig. 5A; p <.0001) and the hilus of the dentate gyrus (p <.0001) were observed in 18–20-month-old transgenic rats (Fig. 5C).

Some microglial cells were seen to localise around AT8-immunopositive neurons (Fig. 5A, centre panel inset), however, there were no differences in microglial numbers at 10 months of age between transgenic and controls rats (Fig. 5B). At later time points (18–20-months), along with extensive proliferation (Fig. 5C), microglia displayed an activated phenotype (Fig. 5D). Additionally, some microglia adopted a distinct, rod-like phenotype, which has previously been described in AD patients and in experimental models of traumatic brain injury. Rod-like microglia ran parallel, either individually or in trains (Fig. 5E), to neuronal projections from the fascioloa cinerea, subiculum, CA1 and layers III and V of the primary somatosensory and entorhinal cortices respectively.

Alterations in astrocytic GFAP expression were also quantified at 10 and at 18–20 months of age. No differences were observed at 10 months when compared with age-matched controls (Fig. 5F, G). However, increases in GFAP total fluorescence and fluorescence area was observed in CA1 and the molecular layer of the dentate gyrus at 18–20-months (Fig. 5F, H).

Extensive myelin degeneration occurs in aged R962-hTau rats

3.6

To determine if a loss of white matter was associated with the degeneration in grey matter, we stained tissue sections with Luxol Fast Blue. This revealed demyelination in the corpus callosum of transgenic rats when compared with control animals at 18–20-months, indicating this pathology occurs secondary to upstream tau aggregation (Fig. 5I).

Statistical analysis was completed using R 3.2.3 (R Core Team, Austria). Independent t-tests were performed, except when the F-statistic was significant, in which case Welch's t-test was applied. If the data violated underlying assumptions of parametric testing, Mann-Whitney U test was used. Where appropriate, multiple comparisons were made with t-tests and corrected with Bonferroni-Holm adjustments. Two-way ANOVA was used to analyse interactions and mixed design ANOVA was used to analyse data consisting of within and between subject factors. To assess the association between two variables, Pearson's correlation was used. All reported values are two-tailed, and overall significance was set at p <.05. Supplementary Table 2 details statistical output.

Results

3

Model generation and relative tau expression

3.1

The expression levels of rodent and human tau were compared by Western blotting using species-specific and total-tau antibodies (Supplementary Table 1). At 3 months of age, R962-hTau rats exhibited two-fold the total tau (Tau5) levels compared to age-matched WT littermates. Total tau hippocampal concentrations were approximately four times higher than age-matched controls between 6 and 15 month time points. Both total tau and human tau (HT7) levels subsequently declined at 18–20 months (Supplementary Fig. 2A). To exclude any effects on endogenous tau expression, we further investigated this at 3 months of age. We determined the increase in cortical tau levels in the R962-hTau rats was due to the expression of transgenic human tau (HT7), since no change in the expression of endogenous rodent tau (T49) was observed (Supplementary Fig. 2B).

Pathological changes in human and endogenous tau occur with age

3.2

To assess if behavioural deficits correlated with human tau levels, we compared the immunofluorescence HT7 signals across regions of interest (CA1, CA3, hilus, amygdala cortex and basomedial nuclei, somatosensory cortex) with each rats' cognitive index score, representing a composite of their performance across all cognitive tests, and brain volume in the same region (Supplementary Fig. 11). While human tau levels did not correlate with cognitive indices [Supplementary Fig. 11B; r = 0.16, p =.70 (NS)], they did correlate with brain volume in the same region (Supplementary Fig. 11C; r = 0.82, p =.012). At 18–20 months of age animals with less intense HT7-immunoreactivity generally had greater brain atrophy and less intense inclusions (Supplementary Figs. 3 and 11A). The same association was present for levels of endogenous tau (T49) across the regions of interest (Supplementary Fig. 11D). T49 levels in R962-hTau rats did not correlate with cognitive index [Supplementary Fig. 11E; r = −0.001, p =.99 (NS)], but positively correlated with brain volume (Supplementary Fig. 11F; r = 0.77, p =.027). These results likely reflect a reduction of brain tau levels following neuronal loss.

Discussion

4

In this report, we describe the production and characterisation of the first rat line transgenic for full-length human tau with the P301S mutation. We demonstrate the progressive, age-dependent increase in the accumulation of filamentous tau, which was upstream of neurodegeneration, myelin abnormalities, gliosis and behavioural deficits. In contrast to the transgenic mouse model where human P301S tau forms filamentous aggregates, aggregates of the R962-hTau rats comprised both human transgenic tau as well as endogenous rat tau in older timepoints.

We investigated the extent and distribution of tau neuropathology present in the R962-hTau rat model between 3 and 20 months of age (Fig. 1). Using antibodies directed against human tau, endogenous rodent tau, and different tau posttranslational modifications, we observed age-dependent alterations in the tau immunoreactivity, reminiscent of the human tauopathies. As predicted by promoter activity and expression, HT7 immunoreactivity was present throughout the forebrain, but absent in control rats (Fig. 1A). An age-dependent increase in human-specific tau immunoreactivity (HT7) was observed to be strongest initially in the hippocampus (Fig. 1B) as well as the somatosensory, entorhinal and piriform cortices (Supplementary Fig. 3). Immunoreactivity was most prominent within cell somas and axons at 3–6-months of age, and appeared more dendritic in nature at later time points, localizing to the neuropil (Fig. 1B). Some immunoreactivity was observed in spinal cord and inferior colliculus, two regions where the CaMKIIα promoter is reportedly not expressed; however, immunoreactivity there was minimal, and no NFT-like inclusions were observed.

Rat tau (T49) became involved in the pathology only relatively late; endogenous aggregated tau was occasionally observed at 6- and 10-months. However, the consistent sequestration of rat tau was not observed until 18–20-months (Supplementary Fig. 4). Rat tau was particularly abundant in inclusions in layers II-III and V of the somatosensory cortex and in hippocampal neurons (Fig. 1B).
```

</details>

## 30. `32e7e71a`

**Question.** What did adapting the Clinical Dementia Rating scale for adults with Down syndrome achieve with respect to the distribution of decline scores?

**Reference answer.** It captured a range of cognitive decline and shifted the distribution of decline scores toward lower or no impairment, by adjusting the original questions for premorbid intellectual and functional ability.

**Answer under review.**

> Adapting the Clinical Dementia Rating scale for adults with Down syndrome shifted the distribution of decline scores toward lower/no impairment by adjusting original CDR questions to take into account premorbid intellectual and functional ability.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
The participant interview portion of the CDR-IDS was difficult to administer to DS adults who were nonverbal or whose speech was limited or difficult to understand. The original CDR was developed for the typical population and in more extreme cases, it cannot capture the full range of disability. Ability to capture cognitive decline across the range of premorbid impairment in DS individuals, from low to high functioning, with a single instrument is a challenge. In the CDR, “thinking and memory problems” are considered interchangeably, but caregiver informants regarded “thinking” and “memory” to be different phenomena and were often unsure how to answer questions that asked about thinking and memory problems together. Some spatial orientation questions were difficult because DS participants in our study were never alone and informants could not evaluate whether the DS adult would be able to find his/her way around familiar streets, for example. Ability to manage a household emergency like a small leak or fire did not seem applicable in our sample, again, since DS adults were almost never alone—even those who live independently have scheduled visitors and structured days. Ability to drive a vehicle or do calculations was absent in our entire sample.

Based on our data and on personal interaction with DS adults and their family members, ongoing research should continue to focus on elements of caregiver report and direct assessment of the DS individual that will optimize differential diagnosis. The primary goal of this study was to adapt the widely used CDR for assessment of dementia in adults with DS. We have shown that such adaptation was successful in capturing a range of cognitive decline and in shifting the distribution of decline scores toward lower/no impairment by adjusting original CDR questions to take into account premorbid intellectual and functional ability. Future work of the CDR-QDS and CDR-IDS should include comparison with existing instruments such as the CAMDEX-DS and DSQIID, with neuropsychological performance, and with other biomarkers, such as positron emission tomography for amyloid or tau.

Conclusions

In addition to these advances, it would be desirable to adapt clinical staging instruments that are widely utilized in scientific and clinical work involving AD dementia in the broader population to afford comparability of assessment and staging for scientific and clinical efforts involving individuals with DS. Therefore, we adapted the Clinical Dementia Rating scale (CDR) for use in DS. The CDR is a semi-structured clinical diagnostic interview that is an integral component of the Uniform Data Set that is used by all federally funded Alzheimer Disease Centers (ADC) to determine the presence or absence of dementia for individuals being evaluated at ADCs. The semi-structured interviews are administered separately to an informant and then to the research participant or patient and focus on capturing intra-individual change from previous cognitive and functional performance levels. An experienced clinician then synthesizes the information from the interview to determine the presence or absence of dementia and, when present, its severity. A CDR score of 0 indicates cognitive normality, whereas scores of 0.5, 1, 2, and 3 indicate very mild, mild, moderate, and severe dementia, respectively.

The primary goal of this project was to determine whether adaptations of the CDR for DS—by both interview and caregiver report—could reliably capture variation among DS patients when implementing new adaptations of an established dementia rating scale.

Methods

Sample

In the first study phase, families with DS adults aged 18 years and older were recruited from the St. Louis ARC, a non-profit organization that provides support and services for individuals with intellectual and developmental disabilities in the St. Louis region. Potential participants were recruited via letters sent to the families by St. Louis ARC. A total of 189 letters were sent asking families to contact the study. Forty families (21.2% response rate) contacted study staff over the telephone regarding their interest to participate. Verbal consent was obtained from the caregiver over the telephone and he/she was then sent the questionnaire version of the modified CDR instrument (CDR-QDS) by postal mail. All forty CDR-QDS instruments that were mailed were received back for evaluation.

Original CDR questions were uniformly modified to ascertain degree of cognitive impairment and the extent to which change had occurred in relation to the participant’s prior baseline. In order to effect this general modification, in some cases, we generated qualifiers for affirmative responses; for example, endorsement of the CDR question “Does he/she have problems with his/her memory or thinking?” triggered a new follow-up question: “Did he/she ALWAYS have a problem with his/her memory or thinking?” (Yes (1)/No (0)). If the DS adult was reported to currently have problems with memory or thinking (current score = 1) but he/she always had this problem (always score = 1), then the CDR-DS rating for cognitive decline was calculated to be zero (current score 1–always score 1 = 0).

In other cases, items related to the DS adult’s current level of functioning were paired with identical companion items eliciting an endorsement of the same item with respect to his/her best ever level of functioning; for example, the CDR question “How often does he/she know the exact day of the month?” has response categories: Usually (0), Sometimes (1), Rarely (2), and Don’t Know. If the DS adult was reported to currently Rarely know the exact day of the month but his/her best ever ability was that he/she Sometimes knew the exact day of the month, then the decline score would be 1 (current score 2–best ever score 1).

In still other cases, we changed response categories; for example, the original CDR question “Rate his/her ability to cope with small sums of money (e.g., calculate change, leave a small tip)” has response categories: No Loss (0), Some Loss (1), and Severe Loss (2). We substituted No Loss with Never Able (0) and Some Ability/No Loss (0) response categories and kept Some Loss (1) and Severe Loss (2). A difference (i.e., adjusted) score could not be calculated for questions with these response options since change relative to premorbid ability was implicit in the response options.

Demographic and clinical data of the 174 participants are described in Table 1. The cohort had a mean age of 74.03 years (SD = 8.55), completed an average of 12.45 years of education (SD = 4.72), and included slightly more females than males (56%). Demographic characteristics were similar across groups in the training set, but age and sex were significantly different between clinical groups in the testing sample. MMSE scores were different across groups in both samples (Supplementary Figure S2). A one-way ANCOVA, controlling for age, sex, and years of education, demonstrated a significant difference in mean logit and algorithm scores for every independent model’s prediction across CN, MCI, and all-cause dementia groups, except for phonemic verbal fluency (see Table 4).

[TABLE: Table 4]

Model performance

The final algorithm in the testing sample with the presented tool resulted in an AUC of 0.93 with an overall accuracy of 88.4%, sensitivity of 87.5%, specificity of 89.2%, and F-score of 0.87 in discriminating CN and impaired groups. The final algorithm in the testing sample obtained an AUC of 0.90 with an overall accuracy of 87.5%, sensitivity of 83.3%, specificity of 89.2%, and F-score of 0.80 in discriminating CN and MCI groups. Using Youden’s Index, the optimal threshold value was determined to be 0.45 for impaired (J = 0.767) and MCI (J = 0.725) groups. Figures 3, 4 present accuracy, F-score, sensitivity and specificity for each threshold value when discriminating CN versus impaired and MCI groups in the whole testing set. Since the selected optimal ensemble ML model is RandomForest, the distribution of scores was non-normal and scores fell close to 0 or 1. Therefore, metrics remained constant between the thresholds of 0.23 and 0.70. The mean squared error obtained in the testing set was 0.10 when distinguishing impaired from non-impaired and 0.114 when distinguishing MCI from non-impaired.
```

</details>

## 31. `c7efee5f`

**Question.** Did COL6A2 co-localize with the deposits in prion-protein cerebral amyloid angiopathy tissue, and where was it located instead?

**Reference answer.** COL6A2 did not generally co-localize with the deposits despite co-occurring in largely the same vessels; it localized more internally, as a component of the basal membrane.

**Answer under review.**

> COL6A2 did not generally co-localize with the deposits but instead localized more internally as a component of the basal membrane.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
Immunoreactivity for COL6A2 is equally present in leptomeningeal vessels in control, AD and CAA tissue. (TIF 3794 kb) Additional file 9:Figure S8. Immunohistochemistry of Amyloid-beta, NDP, COL6A2, APOE and APCS on multiple brain regions of a HCHWA-D CAA type-1 case. Brain tissue of a case exhibiting a hereditary form of CAA type-1 was analyzed by immunohistochemistry of Amyloid-beta, NDP, COL6A2, APOE and APCS. Aβ pathology was confirmed and immunoreactivity associated with CAA type-1 pathology was found present for all markers. Scale bar in upper left picture represents 100 μm. (TIF 34988 kb)

COL6A2 IHC showed some immunoreactivity in control and AD cases which was restricted to leptomeningeal vessels (Additional file 8: Figure S7) and a few large vessels in the brain tissue. In CAA type-1, immunoreactivity for COL6A2 was highly increased and includes brain capillaries and larger vessels. Immunoreactivity was mostly associated with the endothelium and/or the adventitia (Fig. 5g-i). Similar results were obtained using two different antibodies for COL6A2 (data not shown). HTRA1 IHC showed clear overlap with Aβ in both AD and CAA. Compact and diffuse staining was observed related to the vessels in the CAA cases and showed plaque pathology in the AD cases without CAA. Control cases were all negative for HTRA1 (Fig. 5j-l). IHC for APOE resulted in pronounced staining of the vasculature in CAA cases and appeared related to compact deposits as well as more diffuse dyshoric deposits. Also immunoreactivity of APOE was observed in the AD cases related to the Aβ plaques, although the staining was less intense than that related to the vascular amyloid in the CAA cases (Fig. 5p-r). APCS IHC illustrated the presence of this protein in relation with both diffuse and compact Aβ pathology in both the CAA and AD group. However, staining related to the plaque pathology was less intense than that related to the vascular Aβ pathology (Fig. 5m-o).

For quantification of the IHC, images were obtained at sites that, for the AD and CAA cases, had high Aβ pathological burden in nearby sections of the same tissue block. The percentage of positively stained pixels over a total of 5 images from each case was determined. Although this method is semi-quantitative, it allowed a region-specific analysis in line with the tissue obtained by laser capture dissection that was at the basis of the original mass spectrometry analysis. Using IHC quantification we observed strongly increased immunoreactivity in CAA type-1 cases for NDP and COL6A2, and moderate increases for APCS, HTRA1 and APOE, confirming the MS results (Fig. 6).

Specificity in relation to other small vessel diseases

The PrP-CAA tissue was confirmed negative for Aβ pathology (Fig. 7k) and showed positive for Prp (data not shown). NDP immunoreactivity was highly increased and localised to the affected vessels. NDP staining was more pronounced around affected capillaries than at affected larger vessels. COL6A2 immunoreactivity was clearly present around capillaries and larger affected vessels, of which the vascular pathology was clearly observed using haematoxylin. Although co-occurring in largely the same vessels COL6A2 did not generally co-localize with the deposits, but instead localized more internally as a component of the basal membrane. APOE and APCS were also highly present and co-localized with the Prp deposits.

In the white matter no immunoreactivity was seen for Aβ or any of the marker proteins (Fig. 7p-t) in the control case. The CADASIL case showed characteristic pathology in the white matter, thickened vessel walls, in the white matter as is common with this condition. No Aβ pathology was present (Fig. 7u) Mild immunoreactivity for NDP was present and of the assessed proteins COL62A staining was most pronounced. APOE and APCS also displayed mild immunoreactivity related to the affected vessels (Fig. 7v-y).

In hypertension related small vessel disease the presence of COLA6A2 was most prominent while immunoreactivity for NDP, APOE and APCS was low but present (Fig. 7z-ad). Interestingly IHC analysis of the CARASAL cases showed only the prominent presence of COL6A2 in affected vessels while NDP, APOE and APCS were absent.

Taken our data together, from the tested panel of proteins, we recognize COL6A2 as a general small vessel disease marker. NDP, APOE and APCS are most prominent in CAA (type-1 and cotton wool) and Prp-CAA. Involvement of NDP, APOE and APCS in other small vessel diseases is varying from non (CARASAL) to mild (CADASIL). Importantly, NDP is explicitly suitable to evidently separate CAA from Aβ plaque pathology (Table 4).[TABLE: Table 4]

Discussion

To assess the specificity of Aβ, NDP, COL6A2, APCS and APOE in relation to other small vessel diseases we performed additional IHC on cases that present various types of vascular defects, i.e., cotton wool plaque pathology, prion CAA, cerebral autosomal dominant arteriopathy with subcortical infarcts and leukoencephalopathy (CADASIL), hypertension related small vessel disease and Cathepsin A-related arteriopathy with strokes and leukoencephalopathy (CARASAL). IHC was performed on sections that exhibited the relevant pathological characteristics of each disease including an additional CAA type 1 case. Immunoreactivity for Aβ, NDP, COL6A2, APOE and APCS was confirmed in the CAA type-1 case (Fig. 7a-e). Immunoreactivity for these proteins was also assessed and confirmed in case exhibiting hereditary cerebral haemorrhage with amyloidosis Dutch type (HCHWA-D), which is a heredity form of CAA-type-1 (Additional file 9: Figure S8).

In tissue with cotton wool plaques the pathology was confirmed using IHC for Aβ displaying pathology around capillaries and larger vessels with dyshoric changes extending deep into the parenchyma (Fig. 7f). Intense NDP immunoreactivity was observed related to capillaries and the dyshoric changes and to a lesser extend directly lining the larger vessels. COL6A2 showed intense immunoreactivity lining the capillaries and larger vessels (Fig. 7g). IHC for APOE and APCS presented a highly positive, staining that appeared similar to the Aβ staining.

In neural progenitor cells (NPCs) derived from FAD mutant PSEN1 subjects it was found that NDP mRNA is upregulated, but no increase in mRNA was found in AD human temporal lobe. In the retina NDP was found to promote regrowth of capillaries and formation of intra-retinal vessels after oxygen-induced retinal damage. Mice overexpressing NDP, had significantly less vascular loss following oxygen exposure. Mutations in the NDP gene result in Norrie disease, which is primarily an eye disease that leads to blindness. Interestingly, 30–50% of these patients display developmental delay, intellectual disability, behavioural abnormalities, or psychotic-like features. In addition, NDP has been shown to protect neurons against excitotoxicity induced by NMDA. NDP seems to have protective properties for both endothelial cells and neurons, but whether NDP upregulation is beneficial in the context of CAA pathology is unknown.

Our proteomics data show COL6A2 expression in CAA cases, which is supported by a strong increase in COL6A2 immunoreactivity in the affected brain parenchyma. In addition to COL6A2 we also found COL6A3 highly increased in CAA type-1. COL6A2 immunoblotting did not show a significant difference between the experimental groups. This can be explained by the inclusion of leptomeningeal vessels, that express high levels of COL6A2 in all cases in varying amounts in the tissue lysates used for immunoblotting, as shown using IHC. COL6A2 was also found increased in the other small vessel diseases that were included for IHC analysis. This indicates that COL6A2 might be used as valuable indicator of vascular pathology in general, but not specific for CAA type pathology. COL6A2 is a non-fibril collagen and COL6 isoforms are present in various tissues including the vasculature. COL6A2 encodes one of the three alpha chains of type VI collagen, which is found in most connective tissues. Type VI collagen anchors endothelial basement membranes by interacting with type IV collagen. In the brain, collagen VI was shown neuroprotective and its expression increased in animal models of AD.
```

</details>

## 32. `0a03b7a3`

**Question.** What sensitivity and specificity did the time-latency classifier achieve for detecting mild cognitive impairment, and at what latency threshold?

**Reference answer.** At a 70 ms time-latency threshold it achieved 88% sensitivity and 87% specificity.

**Note from the gold set.** the source sentence is malformed -- 'The ROC achieved an AUC of 88% sensitivity and 87% specificity'; an AUC is not a sensitivity. The reference answer reads it as intended, and an answer reproducing the paper's own wording must not be penalised.

**Answer under review.**

> The provided context does not contain the answer.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
Introduction

Alzheimer’s disease (AD) is the most common form of dementia and constitutes a significant public health problem worldwide due to the increasing need of social and economic services for patients and their support systems. A particular clinical challenge in AD and related dementias is identifying the early stages of cognitive decline due to its insidious onset and progression. AD is characterized by neuropathological features that can occur 15 to 20 years prior to noticeable changes in cognition or daily function. Mild cognitive impairment (MCI) often represents a transitional stage between normal aging and dementia, and these individuals are at a greater risk of developing incident AD. Detecting early stages of cognitive decline is paramount for identifying those at greatest risk of progression to dementia and who may benefit from further evaluation and treatment. Improving the detection of early cognitive decline may lead to earlier initiation of disease modifying treatments to preserve independent functioning, which is crucial to a patient’s quality of life.

There currently exist numerous tools to help detect early clinical or pathological signs of MCI/dementia, including thorough clinical workups, neuropsychological evaluations, neuroimaging, and blood and cerebrospinal fluid biomarkers. While imaging and biomarker-based techniques can detect some neuropathological features associated with AD, some are invasive and not widely accessible for the purpose of early detection, and others are still in development. Formal neuropsychological evaluation is often an intrinsic part of the diagnostic process for detecting subtle changes in cognitive function in many centers. However, access to neuropsychological services may be limited due to various geographic, economic, and/or psychosocial factors, including limited access to healthcare resources, and therefore cannot be utilized effectively on a large scale. For these reasons, cognitive screening instruments are used as brief and cost-effective methods to identify individuals who require further evaluation and can be implemented across both primary care and specialized clinical settings. Primary care providers often serve as the first line of medical care for older adults concerned about their cognitive performance, yet physicians in primary care settings report feeling ill-equipped to recognize or document signs of cognitive decline, contributing to gross under-detection of MCI in primary care settings. Nonetheless, current screening methods are not sufficiently sensitive or reliable in identifying clinical signs in the very early stages of dementia, and more precise screening techniques that can capture subtle changes in cognition are needed to identify individuals who may benefit from further evaluation.

In parallel, clinical concepts started shifting, and the early disease stages, before the onset of dementia – which is defined by impairment in daily functioning – got more attention. In the late 1990s, ‘mild cognitive impairment’ (MCI) was introduced as an entity defined by cognitive impairment, but not severe enough to impair daily functioning.5 It became technically possible to assess the presence of amyloid‐β and tau protein in CSF and even using nuclear imaging of the brain. Combining early clinical detection with detecting these biomarkers has triggered a completely new way of thinking about the disease, shifting from a clinical diagnosis based on functioning to a biological diagnosis with or without cognitive dysfunction.

From 2009 onward, this has led to the development of two new conceptual frameworks, by the U.S. National Institute on Aging and the Alzheimer’s Association (NIA‐AA) and an international working group for new research criteria for the diagnosis of AD (IWG).6 According to these frameworks, AD is defined by a pathological process characterized by a specific sequence of brain changes, which develop over a long period of time and may or may not become symptomatic during life. Resulting from these frameworks, a new lexicon and new criteria have been proposed to capture these changing conceptualizations. Biomarkers, which can be detected using CSF analysis, magnetic resonance imaging (MRI) scanning and positron emission tomography (PET) scanning, play an important role in these definitions (Table 1). The main difference between the two conceptual frameworks is that according to the NIA‐AA criteria one can have AD in the absence of any symptoms, whereas, according to the IWG, people without symptoms can only be labelled as ‘at risk for AD’. Both frameworks consider people with MCI and abnormal biomarkers as having AD, irrespective of whether their cognitive impairment is progressive and will lead to dementia.

[TABLE: Table 1]

We evaluated the prediction accuracy of the DNN model in the two-class classification of MMSE (normal, MMSE scores ≥ 24; cognitive impairment, MMSE scores, ≤ 23). We observed a high prediction accuracy with a sensitivity of 75% and specificity of 87%.

Clinical Experience Using the DNN Model

A total of 165 subjects chose the optional DNN-based dementia risk test at the time of their health examination; most subjects had a normal working life and attended the clinic as a regular health check imposed by the employer on the worker. Figure 6 shows the distribution of the classification of cognitive function based on the MMSE predicted by the DNN model. A total of 94 subjects were classified as Class A (normal), while 67 subjects were classified as Class B (suspected MCI). Only four cases were classified as Class C (suspected dementia).

Thirty out of the 165 subjects (mean age, 56.3 ± 9.4 years) were readmitted to the dementia prevention outpatient clinic at the clinic and underwent a detailed examination of cognitive dysfunction involving various neuropsychological tests, including the MMSE, and imaging-based diagnosis using MRI. Most readmitted patients were classified as class B (suspected MCI) or lower. The predicted MMSE scores (26.2 ± 1.1) were significantly lower than the ground truth MMSE scores (28.2 ± 1.8, p < 0 0.05) (Figure 7).

However, in four cases, the predicted MMSE scores (26.9 ± 1.1) exceeded the ground truth MMSE scores (25.3 ± 0.5); the average difference in the MMSE score was −1.7 ± 0.8. Two of the subjects had a neurological disease, such as subarachnoid hemorrhage (SAH). One patient (male, 66 years old) had SAH due to cerebral aneurysm rupture 2 years before the DNN-based dementia risk test; MRA showed an aneurysm of the anterior communicating artery. The patient had undergone endovascular coiling. At the time of examination, there was no motor paralysis, but mild cognitive decline was observed (MMSE score = 25). The blood test data were within the normal range, and the predicted MMSE score was 27.5.

Relationship Between Blood Data and MRI

Demographic and clinical data of the 174 participants are described in Table 1. The cohort had a mean age of 74.03 years (SD = 8.55), completed an average of 12.45 years of education (SD = 4.72), and included slightly more females than males (56%). Demographic characteristics were similar across groups in the training set, but age and sex were significantly different between clinical groups in the testing sample. MMSE scores were different across groups in both samples (Supplementary Figure S2). A one-way ANCOVA, controlling for age, sex, and years of education, demonstrated a significant difference in mean logit and algorithm scores for every independent model’s prediction across CN, MCI, and all-cause dementia groups, except for phonemic verbal fluency (see Table 4).

[TABLE: Table 4]

Model performance

The final algorithm in the testing sample with the presented tool resulted in an AUC of 0.93 with an overall accuracy of 88.4%, sensitivity of 87.5%, specificity of 89.2%, and F-score of 0.87 in discriminating CN and impaired groups. The final algorithm in the testing sample obtained an AUC of 0.90 with an overall accuracy of 87.5%, sensitivity of 83.3%, specificity of 89.2%, and F-score of 0.80 in discriminating CN and MCI groups. Using Youden’s Index, the optimal threshold value was determined to be 0.45 for impaired (J = 0.767) and MCI (J = 0.725) groups. Figures 3, 4 present accuracy, F-score, sensitivity and specificity for each threshold value when discriminating CN versus impaired and MCI groups in the whole testing set. Since the selected optimal ensemble ML model is RandomForest, the distribution of scores was non-normal and scores fell close to 0 or 1. Therefore, metrics remained constant between the thresholds of 0.23 and 0.70. The mean squared error obtained in the testing set was 0.10 when distinguishing impaired from non-impaired and 0.114 when distinguishing MCI from non-impaired.
```

</details>

## 33. `e55293bc`

**Question.** In which cortical region was the N1 difference significantly reduced in the amyloid-infusion mouse model, and what was the trend across the other components?

**Reference answer.** The parietal cortex; across all components in both frontal and parietal regions the standard-deviant differences tended to be attenuated, although not statistically significant.

**Answer under review.**

> The N1 difference was significantly reduced in the parietal cortex in the amyloid-infusion mouse model. The trend across other components showed a marginal tendency of reduced differential ERP in Aβ-infused mice, but this was not statistically significant between groups.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
ERPs. The waveform of the vehicle group produced robust negative deflection via sign tests (difference from zero) performed on the peaks near the N1 period (20–80 ms) in both frontal and parietal cortex (sign test, p = 0.03 same in frontal and parietal cortex), while the Aβ-infusion group failed to show statistically significant negative peaks in both cortices (sign test, p = 0.16 for frontal cortex, p = 0.22 for parietal cortex). In frontal cortex, the maximum negativity was -36.5 ± 4.4 and -25.2 ± 9.6 μV in the vehicle and Aβ-infusion groups, respectively. In parietal cortex, the negative peak was -45.2 ± 7.7 and -25.0 ± 9.1 μV in the vehicle and Aβ-infusion groups, respectively. The differences in early components between the responses to standard and deviant tones were smaller in Aβ-infused mice than in controls in both frontal and parietal cortex. However, a significantly reduced amplitude was found only in the differential N1 component in the parietal cortex (Fig 4, p = 0.03, Kruskal-Wallis test).

Discussion

Recent studies shed light on neuronal dysfunction induced by amyloid-beta levels. In accordance with this perspective, we inspected whether the increase of amyloid β disrupts neural activity related to sensory processing in a mouse model of Aβ infusion. Our aim was to determine whether the auditory oddball paradigm suggested in human patients to diagnose AD, could indicate the severity of AD pathology in the mouse. In our AD model, Aβ-infused mice, the auditory ERP did not discriminate deviant tones from the standard tones. Compared to the control group, Aβ-infused mice tended to exhibit a reduced N1 component in response to deviant sound stimuli in both frontal and parietal regions. Only the parietal region showed a significantly attenuated N1 differential response between deviant and standard tones. The amplitude of the N1 component was correlated with impaired Y-maze test performance.

The shape and latency of auditory ERPs in this study are consistent with previous oddball studies conducted in rodents. The shape of ERP components in the rodent is similar to that in humans, with a systematically short latency. Additionally, researchers have debated whether the ER

ction near the N1 period of differential waveform obtained by subtracting the ERP for the repetitive tone from the ERP for the deviant tone. We compare the differential ERP waveforms for groups. Fig 3 presents the differential ERP traces obtained by subtracting the standard ERP from the deviant ERP in frontal and parietal cortex averaged over vehicle (N = 6) and Aβ (N = 7) infused mice. The grand-averaged differential ERP of the Aβ-infusion group was reduced in both frontal and parietal cortex. However, the differential ERP waveforms were not significantly different between groups (Fig 3, Student’s t-test, p > 0.05).

Peak amplitude of early components and MMN-like activity

The amplitude and latency of the P1, N1, and P2 peaks were determined by maximum or minimum peak detection and are summarized in Table 1. Consistent with the ERP wave forms, a significantly different amplitude in the early components between responses to the deviant and standard tones was observed in the control group, while this difference was destructed in both the frontal and parietal ERP of the Aβ-infusion group (Table 1). In order to analyze the effects of stimulus type and groups, we performed a two-way ANOVA on the peak values of P1, N1, and P2, and groups from the frontal ERP. We found a main effect in the stimulus condition (deviant vs standard, F(1,22) = 6.25, 19.07, and 7.03 for P1, N1, and P2, respectively, all p < 0.05). On the other way, neither the group effect nor the stimulation type x group interaction was found to be significant. The differently elicited ERP between standard and deviant sound were known to relate with auditory sensory memory which important in ability to automatically attend to novel environment. To report the marginal tendency of the reduced differential ERP in Aβ-infused mice, we calculated the amplitude changes to deviant tones in early components, subtracting the amplitude of early components detected in the standard ERP from that of the deviant ERP. Since the shape and latency of the ERP responses to standard and deviant tones are identical in mouse, the MMN-like component in mice is supposed to be the same as the difference in N1 amplitude between deviant and standard

tests to assess working memory ability on the third days of injection (Fig 1A). Total arm entries and percentage of alternations were calculated to assess locomotion and spatial working memory abilities, respectively. We found that the alternation rate was significantly reduced in the Aβ group compared to the vehicle group (Student’s t-test, p = 0.007, Fig 1B), while locomotion was not affected (p = 0.45, Fig 1C). The working memory of 6-week-old ICR male mice was confirmed to be reduced by the ICV injection of Aβ.

ERP waveforms

At one month after ICV injection (32.1 ± 2.1 days, ranging from 29 to 36 day after injection), EEGs were recorded from frontal and parietal cortex during presentation of auditory oddball paradigm. Due to implantation of EEG electrodes and recovery procedures, there was a three-week gap between behavioral and EEG experiments. Fig 2 presents the event-related potentials (ERP) elicited by standard (2 kHz, 90%) and deviant (4 kHz, 10%) sound stimuli averaged over vehicle (N = 6) and Aβ-infused (N = 7) mice. The time windows showing significant differences between responses to standard and deviant sound presentations are marked by a gray shadow overlapping the ERP plots (Student’s t-test, p < 0.05). In the vehicle group, the deviant ERP was significantly different from the standard ERP. In the frontal cortex, there was a significant difference between the two types of ERP in the very early (10–22 ms), early (27–39 ms), intermediate (73–102 ms), and late periods (150–300 ms), which correspond to time windows for the P1, N1, P2, and P3 peaks in rodents. In the parietal cortex, the two ERPs were significantly different during the very early (12–22 ms) and early periods (27–35 ms). Although the averaged ERP traces for the Aβ-infusion group were enhanced in response to the standard tone and reduced in response to the deviant tone compared to the vehicle group, the difference was not statistically significant between the groups. (S2 Fig, Student’s t-test, p > 0.05).

The MMN classically is calculated as a negative defle
```

</details>

## 34. `9dc2a48b`

**Question.** Did COL6A2 co-localize with the deposits in prion-protein cerebral amyloid angiopathy tissue, and where was it located instead?

**Reference answer.** COL6A2 did not generally co-localize with the deposits despite co-occurring in largely the same vessels; it localized more internally, as a component of the basal membrane.

**Answer under review.**

> COL6A2 did not generally co-localize with the deposits but instead localized more internally as a component of the basal membrane.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
The PrP-CAA tissue was confirmed negative for Aβ pathology (Fig. 7k) and showed positive for Prp (data not shown). NDP immunoreactivity was highly increased and localised to the affected vessels. NDP staining was more pronounced around affected capillaries than at affected larger vessels. COL6A2 immunoreactivity was clearly present around capillaries and larger affected vessels, of which the vascular pathology was clearly observed using haematoxylin. Although co-occurring in largely the same vessels COL6A2 did not generally co-localize with the deposits, but instead localized more internally as a component of the basal membrane. APOE and APCS were also highly present and co-localized with the Prp deposits.

In the white matter no immunoreactivity was seen for Aβ or any of the marker proteins (Fig. 7p-t) in the control case. The CADASIL case showed characteristic pathology in the white matter, thickened vessel walls, in the white matter as is common with this condition. No Aβ pathology was present (Fig. 7u) Mild immunoreactivity for NDP was present and of the assessed proteins COL62A staining was most pronounced. APOE and APCS also displayed mild immunoreactivity related to the affected vessels (Fig. 7v-y).

In hypertension related small vessel disease the presence of COLA6A2 was most prominent while immunoreactivity for NDP, APOE and APCS was low but present (Fig. 7z-ad). Interestingly IHC analysis of the CARASAL cases showed only the prominent presence of COL6A2 in affected vessels while NDP, APOE and APCS were absent.

Taken our data together, from the tested panel of proteins, we recognize COL6A2 as a general small vessel disease marker. NDP, APOE and APCS are most prominent in CAA (type-1 and cotton wool) and Prp-CAA. Involvement of NDP, APOE and APCS in other small vessel diseases is varying from non (CARASAL) to mild (CADASIL). Importantly, NDP is explicitly suitable to evidently separate CAA from Aβ plaque pathology (Table 4).[TABLE: Table 4]

Discussion

Immunoreactivity for COL6A2 is equally present in leptomeningeal vessels in control, AD and CAA tissue. (TIF 3794 kb) Additional file 9:Figure S8. Immunohistochemistry of Amyloid-beta, NDP, COL6A2, APOE and APCS on multiple brain regions of a HCHWA-D CAA type-1 case. Brain tissue of a case exhibiting a hereditary form of CAA type-1 was analyzed by immunohistochemistry of Amyloid-beta, NDP, COL6A2, APOE and APCS. Aβ pathology was confirmed and immunoreactivity associated with CAA type-1 pathology was found present for all markers. Scale bar in upper left picture represents 100 μm. (TIF 34988 kb)

COL6A2 IHC showed some immunoreactivity in control and AD cases which was restricted to leptomeningeal vessels (Additional file 8: Figure S7) and a few large vessels in the brain tissue. In CAA type-1, immunoreactivity for COL6A2 was highly increased and includes brain capillaries and larger vessels. Immunoreactivity was mostly associated with the endothelium and/or the adventitia (Fig. 5g-i). Similar results were obtained using two different antibodies for COL6A2 (data not shown). HTRA1 IHC showed clear overlap with Aβ in both AD and CAA. Compact and diffuse staining was observed related to the vessels in the CAA cases and showed plaque pathology in the AD cases without CAA. Control cases were all negative for HTRA1 (Fig. 5j-l). IHC for APOE resulted in pronounced staining of the vasculature in CAA cases and appeared related to compact deposits as well as more diffuse dyshoric deposits. Also immunoreactivity of APOE was observed in the AD cases related to the Aβ plaques, although the staining was less intense than that related to the vascular amyloid in the CAA cases (Fig. 5p-r). APCS IHC illustrated the presence of this protein in relation with both diffuse and compact Aβ pathology in both the CAA and AD group. However, staining related to the plaque pathology was less intense than that related to the vascular Aβ pathology (Fig. 5m-o).

For quantification of the IHC, images were obtained at sites that, for the AD and CAA cases, had high Aβ pathological burden in nearby sections of the same tissue block. The percentage of positively stained pixels over a total of 5 images from each case was determined. Although this method is semi-quantitative, it allowed a region-specific analysis in line with the tissue obtained by laser capture dissection that was at the basis of the original mass spectrometry analysis. Using IHC quantification we observed strongly increased immunoreactivity in CAA type-1 cases for NDP and COL6A2, and moderate increases for APCS, HTRA1 and APOE, confirming the MS results (Fig. 6).

Specificity in relation to other small vessel diseases

To assess the specificity of Aβ, NDP, COL6A2, APCS and APOE in relation to other small vessel diseases we performed additional IHC on cases that present various types of vascular defects, i.e., cotton wool plaque pathology, prion CAA, cerebral autosomal dominant arteriopathy with subcortical infarcts and leukoencephalopathy (CADASIL), hypertension related small vessel disease and Cathepsin A-related arteriopathy with strokes and leukoencephalopathy (CARASAL). IHC was performed on sections that exhibited the relevant pathological characteristics of each disease including an additional CAA type 1 case. Immunoreactivity for Aβ, NDP, COL6A2, APOE and APCS was confirmed in the CAA type-1 case (Fig. 7a-e). Immunoreactivity for these proteins was also assessed and confirmed in case exhibiting hereditary cerebral haemorrhage with amyloidosis Dutch type (HCHWA-D), which is a heredity form of CAA-type-1 (Additional file 9: Figure S8).

In tissue with cotton wool plaques the pathology was confirmed using IHC for Aβ displaying pathology around capillaries and larger vessels with dyshoric changes extending deep into the parenchyma (Fig. 7f). Intense NDP immunoreactivity was observed related to capillaries and the dyshoric changes and to a lesser extend directly lining the larger vessels. COL6A2 showed intense immunoreactivity lining the capillaries and larger vessels (Fig. 7g). IHC for APOE and APCS presented a highly positive, staining that appeared similar to the Aβ staining.

Of the proteins described in Table 3 we selected APOE (approach A), NDP (approach B), HTRA1, APSC and COL6A2 (approach C), based on the fold change or specific expression in the CAA type-1 group compared to the AD and control groups, to confirm our mass spectrometry results. Immunoblotting was performed on whole tissue lysates of the same cases as used for the mass spectrometry analysis. When comparing the CAA group with the control group we found significant differences in NDP expression (Fig. 4). For APOE, APCS and COL6A2, the data showed the same trend of increased abundance in the CAA group as the proteomics data, but the differences did not reach significance. A likely explanation for this is the higher variation of expression of these proteins in the tissue used for immunoblotting, which in contrast to the mass spectrometry exploratory analysis, was not selectively enriched for pathological burden using LCM, and instead included white matter, leptomeningeal vessels and grey matter with a lower pathological burden. To unequivocally demonstrate CAA related expression, we turned to IHC analysis of these same proteins, which, in contrast to immunoblotting, allows region specific analysis similar to the LCM-LC-MS-MS analysis. For this a separate cohort was used consisting of cognitively healthy control cases (n = 8) without any Aβ or tau pathology, 2) AD cases with severe Aβ plaque pathology but no vascular deposits (no CAA) (n = 8) and 3) AD cases with severe CAA type-1 pathology (n = 6).
```

</details>

## 35. `8c43db2d`

**Question.** Which astrocytic structures wrap the neurons containing cisplatin-induced tau deposits, and which endothelial marker also associated with some deposits?

**Reference answer.** AQP4-positive astrocyte endfeet wrap those neurons, and some tau deposits also associated with CD31-positive endothelial cells.

**Answer under review.**

> The neurons containing cisplatin-induced tau deposits are wrapped by the neuron-facing membrane domains of astrocytes, as indicated by AQP4 staining. Some tau deposits also associated with CD31+ endothelial cells.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
closely associated with GFAP+ filaments (Fig. 3C and D) or the perinuclear region of GFAP+ cells indicating the presence of tau deposits intracellularly in astrocytes (Fig. 3D).

Most of the tau deposits in the hippocampus (Fig. 4A-G) and entorhinal cortex (Fig. 4H) colocalized with MAP2, indicating that they are inside neurons. Indeed, high magnification images reveal wrapping of the deposits by MAP2+ microtubules (Fig. 4B-C and E-G). We used aquaporin-4 (AQP4) staining to evaluate the association of tau aggregates with astrocyte endfeet. We observed two patterns of AQP4 staining – channel-like tubular structures representing the perivascular endfeet of astrocytes (p-AQP4) (Fig. 4D, H and 5A-D) and disc-like granular structures indicative of the neuron-facing membrane domains (n-AQP4) of astrocytes (Figs. 4B-C, E-H and 5A-D).

Figure 5

The tau deposits distinctly appeared at the granular, neuron-facing membrane domains of the astrocytes (Figs. 4B-C, E-H and 5A-D). Three-dimensional (3D) orthogonal slice and volume views reveal that the neurons containing tau deposits (as indicated by the colocalization with MAP2) are wrapped by AQP4+ astrocyte endfeet (Fig. 4C, F-G). Some tau deposits also associated with CD31+ endothelial cells. (Fig. 6A and B). Interestingly, meningeal cells lining the brain also contained intracellular aggregates of tau (Fig. 7A and B).

No signs of neuroinflammatory activity or senescence in the brains of cisplatin-treated older mice

We described previously that cognitive impairment in young (8–10-week-old) male and female mice treated with cisplatin was not associated with signs of neuroinflammation as assessed by real-time PCR or RNAseq analysis of hippocampal samples obtained during or at various time points after treatment. In view of the reported increase in neuroinflammation during aging and the localized astro

the cisplatin-induced cognitive deficits. Most importantly, delayed treatment with MSC at one month after the last dose of cisplatin normalized behavior in the PBT and the NOPRT in both sexes.

Discussion

The long-term sequelae of cancer and its treatment include signs of accelerated aging that affect a growing population of cancer survivors. Cognitive decline, a sign of brain aging, is amongst the most devastating of these adverse consequences. Increasing evidence indicates that chemotherapy for cancers outside the nervous system increases the risk of cognitive impairment. Nevertheless, multiple epidemiologic studies have shown that there is an inverse relation between cancer and Alzheimer disease [–]. Although this seems counterintuitive, cognitive decline associated with accelerated aging may well be independent of the development of Alzheimer disease. Indeed, a study in patients treated for colorectal cancer showed that chemotherapy increased the risk of cognitive decline, while in the same cohort the risk of developing Alzheimer disease was reduced.

Here, we investigated the effect of the chemotherapeutic cisplatin on two signs of accelerated aging; cognitive decline and the formation of tau deposits in the brain. We show that treatment of 9-month-old mature adult male and female mice with cisplatin accelerates the formation of tau deposits in the brain, a hallmark of brain aging. The tau deposits in the brain of cisplatin-treated mice are restricted to the hippocampus and entorhinal cortex. Deposits of tau colocalized with syndecan-2 and were mainly found inside neurons that were surrounded by the aquaporin 4 positive neuron-facing membrane domains of astrocytes. In search for an intervention, we demonstrate that nasal administration of bone marrow derived MSC at 48 and 96 hours after completion of chemotherapy prevented tau cluster formation and normalized cognitive function in male and female mice. Importantly, nasal MSC administration also prevented tau cluster formation and cognitive deficits when treatment was delayed until one month after completion of cisplatin treatment.

In humans, accumulation of tau deposits is thought to be part of normal brain aging and is strongly linked to age-related cognitive decline [, –]. These tau depositions are first developing in the entorhinal cortex and spread to the hippocampus and other brain areas later in life. Mice also develop tau deposits in the hippocampus during healthy aging and these deposits are first detectable at an age of 12–14 months. Consistently, we detected sparse tau deposits in the hippocampus of control mice

platin treatment is known to induce oxidative stress because it damages neuronal mitochondria. Preventing this mitochondrial damage using a small compound that prevents mitochondrial accumulation of p53, pifithrin-μ, also prevented cisplatin-induced cognitive deficits in young mice. It may well be possible that the cumulative effect of the normal age-related oxidative stress surge and the mitochondrial damage caused by cisplatin causes the formation of tau deposits in the brain of older mice. In support of this model, we showed that nasal administration of MSC reverses the neuronal mitochondrial damage in cisplatin-treated young mice. In vitro, MSC transfer healthy mitochondria to neuronal precursors damaged by cisplatin via actin-based inter cellular structures. This intercellular transfer of mitochondria restores mitochondrial health and neuronal survival. If nasally administered MSC would act similarly in older mice treated with cisplatin, this would alleviate oxidative stress which may well underlie the prevention of the signs of accelerated aging in our current study. We also showed that cisplatin induces peripheral neuropathic pain which is reversed by nasal administration of MSC. We recently published that MSC from IL-10 knockout mice were incapable of reversing neuropathic pain and that intact MSC are capable of inducing IL-10 production in macrophages. Both mitochondrial deficits and IL-10 deficiency can contribute to tau pathology and neuroinflammation. Therefore, we propose that nasal MSC treatment may prevent tau pathology by normalizing brain mitochondrial health and/or IL-10 production.

We show here that the tau deposits are lined by neuron-facing membrane AQP4 in astrocytes. This n-AQP4 has been shown to play a critical role in the clearance abnormal tau from neurons during normal aging via drainage. Notably, aging is associated with a decrease in the capacity of the meningeal lymphatic system to clear damaged proteins. Such reduced clearance may promote the accumulation of tau deposits in the brain and may explain the association of neuronal tau deposits with n-AQP4 of older cisplatin-treated mice, while younger mice may well be capable of clearing the abnormal tau.

Our current finding that cisplatin-induced cognitive deficits are not associated with signs of inflammation in the brain is in line with our previous studies in older female and young male and female mice. Using RNA sequencing, RT-PCR analysis or

at an age of 11–12 months. In addition, we show that there are some tau deposits in the entorhinal cortex of 11–12 months-old mice. Treatment of 9-month-old mice with cisplatin markedly increased the number of tau deposits in both males and females as examined 2 months later. Similar to what has been reported during natural aging, the tau deposits in the brain of cisplatin-treated mice do not label with the AT8 antibody recognizing hyperphosphorylated tau. In contrast, brain AT8 reactivity is increased in mouse models of Alzheimer disease. Moreover, we show that syndecan-2 always colocalizes with the tau deposits in cisplatin-treated mice. No tau− syndecan+ clusters were detected. This colocalization is reminiscent of similar protein deposits containing both tau and syndecan-2 in the brain of SAMP8 mice, a well-established model of accelerated aging. Collectively, our current and previous findings indicate that treatment of mature adult mice with cisplatin induces signs of accelerated aging that are prevented by nasal administration of MSC.

Our finding that nasal administration of MSC after completion of cisplatin treatment prevents the formation of tau deposits and the associated cognitive deficits in older mice is especially important from a translational point of view. There are no FDA-approved interventions to manage the cognitive decline that is frequently reported by patients treated for cancer. Currently, most pre-clinical studies aiming at identifying treatments for chemotherapy-induced cognitive decline have been performed in young mice. However, most patients treated for cancer are older adults and aging may affect the efficacy of treatment. It is therefore very encouraging that nasal administration of MSC does not only treat cognitive decline in young, but also in older cisplatin-treated mice. Additional clinical relevance lies in our finding that nasal administration of MSC can be delayed for at least one month after the last dose of cisplatin. We showed previously that nasally administered MSC enter the brain of cisplatin-treated young mice where they affect the brain transcriptome, restore synaptosomal mitochondrial function and reverse abnormalities in white matter and synaptic integrity.

It remains to be determined how cisplatin treatment accelerates formation of tau deposits in the brain of older mice, but not younger mice and how MSC prevent this tau pathology. Recent studies in show that during healthy aging there is a surge in oxidative stress in brain neurons at an age of approximately 40 weeks (9 months). Cis
```

</details>

## 36. `a5377343`

**Question.** How many proteins were found to be consistently enriched in amyloid plaques relative to neighbouring non-plaque tissue in both Down syndrome and early-onset Alzheimer's disease?

**Reference answer.** A core group of 48 proteins was consistently enriched in plaques compared with neighbouring non-plaque tissue in both conditions.

**Answer under review.**

> 22 proteins were found to be consistently enriched in amyloid plaques relative to neighbouring non-plaque tissue in both Down syndrome and early-onset Alzheimer's disease.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
significantly enriched in plaques in comparison to non-plaque tissue. While our immunohistochemistry validation results strongly suggest that some of these novel plaque-associated proteins interact with Aβ, future studies are required to confirm this.

Direct comparison of the amyloid plaque proteome in EOAD and DS showed that amyloid plaques in the two subtypes of younger onset AD had a very similar plaque protein composition. This shows that despite the different disease initiating factors, the resulting amyloid plaques still largely contain the same proteins. While some proteins were enriched to a much greater extent in amyloid plaques in either DS or EOAD (e.g. SMOC1), the trend for enrichment in both subtypes was highly similar. It is still unclear how these relative plaque protein differences influence AD pathogenesis. Future mechanistic studies examining how each of these proteins influence Aβ aggregation or clearance are needed. Future proteomic studies examining whether these major plaque enriched proteins are also enriched in other subtypes of AD (such as late onset AD, rapidly progressive AD or familial EOAD) would also potentially provide insight into differences into the rate, topography or type of plaque pathology between these subtypes.

In conclusion, we provide a new resource for the AD field that comprehensively characterizes proteins that are enriched in amyloid plaques in multiple subtypes of AD. We propose that these consistently enriched amyloid plaque proteins provide insight into the mechanisms driving amyloid plaque development in AD and are potentially novel drug targets and/or biomarkers for AD.

Supplementary Information

Additional file 1: Table S1. Total imputed dataset. Table S2. Unimputed data. Table S3. Proteins enriched in plaques in both EOAD and DS (used to generate Figs. 2 and 4). Table S4. Proteins uniquely enriched in plaques in EOAD. Table S5. Proteins uniquely enriched in DS plaques. Table S6. Chromosome 21 proteins identified in our proteomic analysis. Table S7. DS vs EOAD plaque protein differences.Additional file 2: Figure S1. APOE genotyping. (A) Schematic diagram of the APOE genotyping methodology. Six scrolls of 8 µm were sectioned from FFPE blocks and DNA was isolated with the automated QIAsymphony SP. An endpoint PCR was performed, samples were resolved in a 2% agarose gel and amplified DNA was purified from

DS resulted in any major differences in plaque associated proteins. Our proteomic analysis identified 22 proteins with genes on chromosome 21 (Additional file 1: Table S6). Of these, only three proteins were enriched in plaques in DS: APP, ITGB2 and COL18A1. APP was commonly enriched in plaques in both EOAD and DS. While ITGB2 and COL18A1 both had higher levels in plaques in comparison to non-plaques in EOAD, their level did not meet our criteria for designation as “enriched”. Therefore, our results suggest that the triplication of chromosome 21 is not necessarily associated with enrichment of those gene products in plaques, but rather may enhance the enrichment of selected proteins in plaques.

Validation: comparison with previous proteomic studies

Only one prior study has examined the proteome of amyloid plaques in comparison to surrounding non-plaque tissue. This study identified proteins that were enriched in amyloid plaques in late-onset AD and preclinical AD. Despite the power of their dataset being limited by a small sample size (n = 3 cases/group, pooled prior to mass spectrometry) and the different subtypes of AD analyzed in their study in comparison to ours, we were pleased to see that many of our plaque enriched proteins were validated in this previous study. 43 proteins were identified in both our study and enriched in late-onset AD plaques in Xiong et al. 26/43 commonly identified proteins were significantly enriched in either DS or EOAD plaques (Additional file 1: Table S1). The majority of the remaining proteins were also increased in plaques in our study, however they did not reach the criteria for significance in our study. All of the top 10 most highly enriched proteins in plaques in DS and EOAD in our study were also enriched in plaques in late onset AD (Fig. 5).

Xiong et al. also identified 78 proteins that were enriched in plaques in preclinical AD. 53 of these proteins were also identified in our study, of which, 30 were enriched in DS or EOAD plaques (Additional file 1: Table S1). The most notable protein that was not enriched in preclinical AD plaques was COL25A1, which was the most highly enriched protein in both DS and EOAD plaques in our study and was enriched in late-onset AD plaques in Xiong et al.. This suggests that COL25A1 may only become enriched in plaques at a later stage of

.g. limbic predominant vs hippocampal sparing vs typical), by rate of progression (e.g. rapidly progressive AD vs typical AD), or more recently using unbiased ‘omics approaches. We recently showed that plaques in rapidly progressive AD had a significantly different proteome than plaques in typical sporadic AD, suggesting that the amyloid plaque proteome is not consistent in all AD subtypes and that these plaque protein differences may contribute to the development of different subtypes of AD. It is currently unclear whether amyloid plaques in other AD subtypes also have significantly different protein composition, or whether these plaque protein differences were unique to rapidly progressive AD.

The aim of this study was to compare the amyloid plaque proteome in two subtypes of early onset AD: sporadic early onset AD (EOAD) and Down Syndrome (DS) with AD. Between 5 and 10% of AD cases are considered early onset. Of these, only approximately 10% are caused by APP, PSEN1 and PSEN2 mutations. The cause of the remaining ~ 90% of EOAD cases is unknown and these cases are therefore characterized as sporadic EOAD. It is currently unclear if the same molecular mechanisms drive sporadic EOAD cases and late-onset AD. DS with AD is another prevalent subtype of early onset AD. Adults with DS have a very high risk of developing AD, which is thought to be driven by the triplication and consequent overexpression of APP in DS. People with DS develop AD associated neuropathology very early in life. Accumulation of soluble Aβ has been observed in fetuses with DS. Intraneuronal Aβ is present in children as young as 1 year old, which is followed by the development of diffuse plaques by the age of approximately 12 years. Mature plaques are commonly present in the 30’s and advanced AD neuropathology is present by the 40’s. The progressive accumulation of amyloid and tau pathology in DS largely follows a similar pattern to that observed in AD, albeit with more plaques in the striatum and thalamus and a higher plaque density overall in DS in comparison to AD. Multiple studies have shown that plaques in DS contain similar post-translationally modified Aβ species as observed in AD, including Aβ phosphorylated at serine 8 and pyroglutamate modified Aβ [, –], however it is still unknown if plaques in DS
```

</details>

## 37. `90b1752f`

**Question.** What is the Drosophila orthologue of TMCC2 called, and what does it protect against?

**Reference answer.** It is called Dementin, and it protects against the developmental and behavioural defects caused by ectopic expression of human APP in flies.

**Answer under review.**

> The provided context does not contain the answer.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
TMCC2 was initially identified as a molecule that may link APOE status to APP processing. In this first study of TMCC2 in the human brain, we observed an association of TMCC2 immunoreactivity with that of APP, complementing previous observations of TMCC2‐APP complexes in the rat brain and human cells. We also observed that this association is influenced by the APOE genotype within neuronal dystrophies of late onset AD. The evolutionarily conserved nature of this interaction indicates that the physiological functions of TMCC2 and APP are expected to overlap. TMCC family members are found within endomembrane systems, though they may also be present at the cell surface in vivo, perhaps affecting the biology of APP in cell–cell interactions and synaptogenesis. Emerging data point to converging roles in brain development and neuronal synapse homeostasis that may be disrupted by mutation of TMCC2 or its orthologues as well as potentially by its interaction with apoE4. During the preparation of this manuscript, it was revealed that targeted alleles of mouse TMCC2 indicate a role for TMCC2 in cell survival, where TMCC2 deficiency leads to selective adult‐onset cell death in the nervous system, including auditory hair cells, suggesting a role for TMCC2 in the survival of neural cells.

Given the association of TMCC2 with both APP and apoE, and the established roles of these two proteins in AD pathogenesis, we investigated TMCC2 distribution in 19 AD cases having different genetic susceptibilities, either five cases each of APOE3 or APOE4 homozygotes in late onset AD as well as in five age‐matched controls, together with early onset AD associated with Down syndrome (three cases) or familial AD associated with APP mutated at Val717 (six cases).

To investigate TMCC2 in late onset AD and whether this is influenced by APOE genotype, we examined TMCC2 protein levels and cellular distribution in five APOE3 homozygous cognitively healthy human brains with an average age of 85 (range 82–90), five AD cases homozygous for APOE3 pathologically diagnosed with AD (Braak stages IV and V) with an average age of 77 (range 70–81), and five AD cases homozygous for APOE4 and diagnosed with AD (Braak stages V and VI), with an average age of 76 (range 71–89). Case details are provided in Table 1.

Using a rabbit antibody previously validated against mouse and rat brain‐derived TMCC2 (antibody 94), we detected a set of three bands in human brain homogenates by western blot. All bands migrated with an apparent molecular weight close to or greater than that predicted from the amino acid composition of TMCC2 (77.5 kDa; Figure 1A). A similar pattern was observed using a separate independently generated antibody (antibody 11193), which, however, had reduced specificity compared to antibody 94 (Figure S1A).

Taken together, the above prior findings in vitro and in Drosophila suggested that TMCC2 would demonstrate an interaction with APOE genotype and/or an association with AD pathology. Here, we test this hypothesis and report the first investigation of TMCC2 expression in the human brain. We examined TMCC2 immunoreactivity in late onset AD cases stratified by APOE genotype and age‐matched non‐demented controls, as well as in early onset AD cases associated with mutations in APP or Down syndrome. We found that TMCC2 associates with characteristic pathologies of AD in both early and late onset AD, and shows variation in apparent molecular weight according to brain region as well as by APOE and/or dementia status. We further found that antibodies to TMCC2 detect a pathological feature of Down syndrome AD that binds amyloid‐sensitive dyes, previously referred to as ‘fibrous plaques’ or ‘bird's nest plaques’, but without being previously assigned to a protein.

MATERIALS AND METHODS

2

Human brain

2.1

All procedures performed in studies involving human tissue were in accordance with the ethical standards of the 1964 Helsinki Declaration and its later amendments. Ethical approval was granted by the Brains for Dementia Research City and East National Research Ethics Service committee (08/H0704/128+5) and specimens provided by the Manchester Brain Bank, Salford, UK, and London Neurodegenerative Diseases Brain Bank—King's College London. Cases were anonymized, but information is provided regarding APOE genotype, sex, age at death and neuropathology (Table 1).

[TABLE: TABLE 1]

Western blots and immunofluorescence

2.1.1

For immunostaining, 7‐μm‐thick sections were cut from formalin‐fixed paraffin‐embedded blocks from the same cases as used in immunoblot protocols. Following dewaxing, antigen retrieval was performed with 80% formic acid for 20 min, rinsing in water, microwaving to boiling in sodium citrate pH 6.0 and kept in hot citrate buffer for 10 min following heating. Blocking was performed with normal goat serum (DAKO, Cambridgeshire, UK) for 1 h at room temperature. For dual immunostaining, anti‐TMCC2 was used at 1/300, and 4G8 or C1/6.1 at 1/500. Secondary antibodies were Alexa‐Fluor‐488‐conjugated goat anti‐rabbit and Alexa‐Fluor‐546 or Alexa‐Fluor‐568‐conjugated goat anti‐mouse, from Invitrogen, and incubated for 1 h at room temperature. Methoxy‐X04 was used at 10 μM for 20 min in phosphate‐buffered saline and autoflourescence quenched with Sudan black. Fluorescent images were collected on a Zeiss Axio Imager Z2 LSM 800 microscope and processed using Zeiss ZEN software and ImageJ.

Quantification of co‐localization

2.1.2

Immunohistochemical staining for TMCC2 in the temporal cortex showed primarily a neuronal pattern (Figure 1B), consistent with previous detection in primary neurons and proposed roles of TMCC2 in endomembrane systems. TMCC2 forms a complex with APP in transfected human cells and in the rat brain, where a large fraction of TMCC2 exists in a complex with APP. We therefore examined human brain sections for both TMCC2 and APP by double immunofluorescence using antibody 94 to TMCC2 and antibody C1/6.1, which binds the C‐terminus of APP (residues 676–695 of APP695). We found a high degree of similarity between the staining patterns for both (Figure 1B). Similar results were obtained using antibody 22C11, which recognises the N‐terminal ectodomain of APP (Figure S1B). In non‐demented brains, TMCC2 immunoreactivity was rarely distinct from that for APP, whilst APP staining exists predominantly together with TMCC2 but is occasionally separated (Figure 1B, arrow), suggesting a dynamic association between TMCC2 and APP. Association of TMCC2 with APP may not be limited to the central nervous system: TMCC2 and APP immunoreactivity was also detected in the lumen of blood vessels (Figure 1B, asterisk), consistent with high expression of APP in platelets with likely co‐expression of TMCC2 as TMCC2 may also function in haematopoiesis, being strongly linked to platelet and erythrocyte levels in genome‐wide association studies; a blood‐specific isoform of TMCC2 (RefSeq NM_001297613) that may influence erythrocyte differentiation is translated from an alternate mRNA to yield a predicted 52 kDa protein that would be detected by antibody 94. TMCC2 has been identified in several proteomic databases for platelets and mature erythrocytes.
```

</details>

## 38. `71dff36c`

**Question.** What CSF tau threshold defined tau positivity in the linear mixed-effects models of vascular biomarkers?

**Reference answer.** Tau positivity was defined as a value above 24.8 pg/mL.

**Answer under review.**

> The provided context does not contain the answer.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
Demographic characteristics were compared using t tests, χ2 tests, and Mann–Whitney U tests. Associations of tau markers with age, sex, and apolipoprotein E (APOE) ɛ4 status were examined using Pearson correlations or t tests. Associations between tau markers were examined using linear regressions adjusted for age, sex, and time between PET and blood collection. We examined between-group differences in tau markers using age- and sex-adjusted analysis of covariances. We performed receiver-operating-characteristic analyses to compare tau marker accuracies in discriminating cognitive stage (SCD vs. MCI/AD) and preclinical Aβ status (SCD Aβ-negative vs. SCD Aβ-positive). Differences between areas under the curve (AUCs) were tested using DeLong tests.

Next, we investigated associations of tau markers with cognitive decline using age-, sex-, and education-adjusted linear mixed models (LMMs) with subject-specific intercepts. For all LMMs, a random slope was added when it improved model fit by comparing the Akaike information criterion using χ2 statistics. Tau marker (tau PET or plasma pTau181), time (tau PET or blood collection as T = 0), and an interaction term of tau marker × time were entered as fixed variables and neuropsychological test performance as a dependent variable. For all LMMs, we used separate models per tau marker and per cognitive test. Furthermore, tau markers and cognitive scores were scaled within each LMM to compare effect sizes. The fixed effect of tau marker was interpreted as the cross-sectional association, and the fixed effect of tau marker × time was interpreted as the longitudinal association. P values were corrected for multiple testing by applying the 10% false-discovery rate (FDR).

The primary cognitive outcome was also analyzed using CSF biomarkers on the same subjects and results were compared between CSF and plasma models using the AIC. The larger the difference in AIC is between two models, the less plausible it is that the model with higher AIC provides the best fit–. The risk of AD dementia was not analyzed using CSF biomarkers because these biomarkers were consulted by neurologists during diagnosis, leading to potential circular reasoning.

Sensitivity analyses were also performed with (a) MMSE as the cognitive outcome instead of PACC, (b) all-cause dementia as the clinical outcome instead of AD dementia, and (c) APOE ε4 status (one or more ε4 copy versus zero ε4 copies) included as an additional predictor in the basic model.

All analyses were performed using the ABA (“Automated Biomarker Analysis”) package (v1.0.1) written in the R programming language (v4.0.0). All statistical tests were two-sided with a significance level of 0.05.

Reporting summary

Further information on research design is available in the Nature Research Reporting Summary linked to this article.

Supplementary information

Supplementary Information

Reporting Summary

Biomarker cutoffs were derived from levels at baseline using the Youden index procedure to maximize separation of CU individuals without a positive CSF Aβ42/Aβ40 (n = 350) who did not convert to AD dementia versus MCI (n = 111) and CU (n = 30) individuals who did convert to AD dementia). For plasma Aβ42/Aβ40, the resulting cutoff was 0.066 pg/mL. For Plasma P-tau217, the resulting cutoff was 0.199 pg/mL. For plasma NfL, the resulting cutoff was 22.3 pg/mL. To note, binarized biomarker status was used for visualization purposes only to demonstrate theoretical differences in outcome trajectories.

Statistical analysis

Linear mixed-effects (LME) modeling was used to model longitudinal PACC, with five models tested in total: a basic model (age, sex, education), the basic model plus each of the three plasma biomarkers added separately (i.e., basic model + Aβ42/Aβ40; basic model + P-tau217; basic model + NfL), and the basic model plus all three plasma biomarkers together. LME models had random intercepts and random slopes with an unstructured covariance matrix. Normality of model residuals was confirmed to ensure appropariateness of LME modeling. Cox regression was used to model clinical conversion to AD dementia with the same models fit as above; all participants were right censored at last follow-up visit or at clinical conversion. A power analysis was performed in which the reduction in sample size needed to achieve 80% power to observe a 30% reduction in cognitive decline or clinical conversion was calculated in a scenario where each biomarker was used individually (based on univariate thresholds) or combined (based on a fitted multivariate model) to screen individuals for trial inclusion and in order to enrich the trial population for the relevant outcome. All biomarkers were treated as continuous variables after being log-transformed prior to any analysis.

Next, we examined whether baseline scores from unsupervised memory assessments were associated with future cognitive decline rates in the mPACC and whether a combination of a blood‐based biomarker and digital cognitive markers would outperform individual measures in predicting cognitive decline. Recent work has shown that plasma p‐tau217 was associated with cognitive decline as well as disease progression., To that end, we derived participant‐specific mPACC slopes from linear mixed‐effects model with random intercepts and slopes and ran hierarchical linear regression models with plasma p‐tau217 and remote memory measures as predictors to test which model best predicted mPACC decline across 5 years.

Adjusting for covariates, cognitive outcomes for MDT‐S and ORR‐DR as well as p‐tau217 but not MDT‐O were significantly associated with mPACC slopes (see Tables 2 and 3, see also Table S2 for individual longitudinal linear mixed‐effects models for each marker).

[TABLE: TABLE 2]

[TABLE: TABLE 3]

We next aimed to define an optimal combination to predict mPACC slopes. The best combination model for prediction of mPACC slopes (i.e., the model with the lowest AIC) included plasma p‐tau217 (β [SE] = −0.024 [0.005]; p < 0.001), MDT‐S (β [SE] = 0.174 [0.032]; p < 0.001), age (with higher age associated with worse mPACC slopes; β [SE] = −0.003 [0.001]; p = < 0.001), sex (with male sex associated with worse mPACC slopes; β [SE] = 0.044 [0.013]; p < 0.001), and education (β [SE] = −0.004 [0.002]; p = 0.069; AIC for the overall model: −474; R 2 = 0.31, see Table 2 “Digital Cognitive Marker + BBM”). This model was also better than both the Digital Cognitive Marker and the BBM model as indicated by a lower AIC.

The overarching aim of this study was to perform a head-to-head comparison between plasma pTau181 and tau PET in a cohort of participants with subjective cognitive decline (SCD) and MCI or dementia due to AD (MCI/AD) against several clinically relevant measures. We examined their accuracies in discriminating cognitive stage (MCI/AD vs. SCD) and preclinical Aβ status (SCD Aβ-positive vs. SCD Aβ-negative), their associations with cross-sectional and longitudinal cognition, their longitudinal changes over time, and longitudinal tau biomarker relationships with longitudinal cognition.

MATERIALS AND METHODS

Participants

This study included all individuals from the Amsterdam Dementia Cohort and SCIENCe project with a clinical diagnosis of SCD (n = 50), MCI due to AD (n = 10), or probable AD dementia (n = 50) who underwent 18F-flortaucipir (tau) PET and had a plasma sample biobanked within 12 mo from tau PET (median, 5.0 mo; interquartile range, 4.4 mo) (–). The supplemental materials available at http://jnm.snmjournals.org provide details (–). SCD participants underwent 18F-florbetapir (Aβ) PET for visual assessment of Aβ status for research purposes. All MCI or AD dementia participants were biomarker-defined as Aβ-positive by means of abnormal cerebrospinal fluid Aβ1-42 biomarkers (according to routine thresholds) or a positive Aβ PET visual read. MCI and AD dementia participants were grouped into a single MCI/AD group. The study protocol was approved by the institutional review board of the Amsterdam UMC. All participants provided written informed consent.

Blood Sampling and Analyses

Ethylenediaminetetraacetic acid plasma samples were collected through venipuncture. A subset (n = 40) had 2.2 ± 0.5 y of follow-up samples available.
```

</details>

## 39. `93bc6e1a`

**Question.** Which novel MHC-I partner does amyloid-beta-oligomer destabilisation of the synaptic MHC-I-beta2M complex impair the interaction with, and what reversed the resulting signalling impairment?

**Reference answer.** NCAM-1; inhibiting the amyloid-beta-induced destabilisation of the MHC-I complex with SCT reversed the neuronal signalling impairment.

**Answer under review.**

> The amyloid-beta-oligomer destabilization of the synaptic MHC-I-beta2M complex impairs the interaction with NCAM-1. This impairment was reversed by restoring the MHC-I complex, as demonstrated by the SCT-mediated restoration, which reversed the signaling impairment.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
Discussion

The present study revealed that Aβ oligomers destabilizes synaptic MHC-I-β2M complex, impairing the interaction with NCAM-1, a novel MHC-I partner. We here further showed that inhibiting the Aβ-induced destabilization of MHC-I complex by SCT can reverse the neuronal signaling impairment, harnessing a novel therapeutic strategy.

Although studies have been made about the role of neuronal MHC-I in synaptic plasticity, little was known about MHC-I function in neurological diseases. Especially, the connection between MHC-I function and its role in AD remained unclear, despite genetic analyses showing an increased frequency of some MHC-I alleles in individuals with AD. We here found that the unstable β2M-free MHC-I heavy chain was increased in AD brains (Fig. 2). The oligomeric Aβ was largely responsible for the destabilization of neuronal MHC-I-β2M complexes (Fig. 1). Aβ treatment caused MHC-I-β2M complex to degenerate into soluble β2M and β2M-free MHC-I heavy chain, leading to rapid internalization of MHC-I heavy chain followed by lysosomal degradation (Fig. 1). This β2M-free MHC-I heavy chain was also found to regulate synapse density negatively in glutamatergic neurons, which may be related with synapse loss in AD brains. MHC-I was also recently reported to be involved in the pathogenic mechanisms of the strongest risk factor of sporadic AD, apolipoprotein-E4.

Since NCAM1 is a novel interacting partner of neuronal MHC-I-β2M complex (Fig. 3) and MHC-I-β2M is destabilized by Aβ oligomers and in AD brains (Figs. 1, 2), we speculated that the interaction of NCAM1 with MHC-I-β2M complex is also deregulated. As expected, co-immunoprecipitation assay showed reduction in the amount of NCAM1-MHC-I-β2M complex in AD brains (Fig. 4A, B). In primary neurons, NCAM1 co-localized with MHC-I at the surface of the soma or dendrites, however Aβ oligomer reduced the co-localization intensity between MHC-I and NCAM1 or each protein levels (Fig. 4C–E). Aβ treatment reduced the amount of NCAM1 interacting with MHC-I by about 50% relative to control in primary neurons (Fig. 4F, G). Aβ treatment also reduced CREB phosphorylation, which is part of the final cascade of NCAM1 signaling (Fig. 4H, I), suggesting that the MHC-I–β2M complex is important for interacting with NCAM1 and activating its signaling. Together, these observations suggested that Aβ-mediated destabilization of MHC-I-β2M complex eventually impairs the formation of NCAM1-MHC-I-β2M complex, subsequently dysregulating NCAM1 signaling.

Stabilization of MHC-I-β2M complex rescued Aβ-mediated MHC-I depletion and dysregulation of NCAM1-MHC-I interactions

Aβ oligomers induced extracellular release of β2M which was dissociated from surface MHC-I-β2M complex (Fig. 1E, H). Several proteomics analyses have identified β2M as a potential biomarker in the CSF of patients with AD. Interestingly, β2M is a pro-aging factor that impairs cognitive function and neurogenesis, implying relations with AD. β2M could induce cognitive decline via neuroinflammation through toll-like receptor 4 (TLR4). Hence, the increased release of β2M downstream from Aβ-induced dissociation of MHC-I-β2M complex (Fig. 1) could be related with neuroinflammation and neurodegeneration in AD. How Aβ oligomer dissociates MHC-I-β2M complex is yet uncertain. Aβ oligomer might dissociate MHC-I complex directly or indirectly via unknown mechanisms. Leukocyte immunoglobulin like receptor B2 (LilrB2) is a well-known binding partner with MHC-I. Aβ oligomers bind to LilrB2, which might be a way of dissociating MHC-I-β2M complex indirectly. LilrB2 has a binding preference to β2M-free MHC-I heavy chains rather than the MHC-I-β2M complex in vitro. Additional studies are required to assess the detailed mechanism of MHC-I dissociation and toxic effects of Aβ-mediated extracellular β2M.

Although several meta-analyses of genetic risk factors for Alzheimer’s disease (AD) have suggested that MHC-I alleles, specifically HLA-A2.1 and HLA-B7, are associated with AD pathology, the relationship between MHC-I with AD remains unclear because of contradictory reports in differential populations. Amyloid-β (Aβ) peptide is a major pathological factor in synaptic dysfunction. Specifically, oligomeric Aβ dysregulates activity of several synaptic receptors. α-amino-3-hydroxy-5-methyl-4-isoxazolepropionic acid (AMPA) and n-methyl-d-aspartate (NMDA) receptors, whose function and trafficking are regulated by synaptic MHC-I, are, in turn, negatively regulated by Aβ peptide in AD. Additionally, PirB which is a MHC-I receptor expressed in synapses of hippocampal neurons, and is involved in synaptic plasticity during CNS development [–], was identified as an amyloid-β (Aβ) receptor and has been implicated in AD pathology mediated by dysregulated synaptic plasticity with cofilin activation. These findings suggest that MHC-I may have a putative role in AD pathophysiology.

We here addressed this point and revealed that Aβ destabilizes MHC-I complex resulting in decrease of NCAM-1 signaling but restoring MHC-I complex reverses its signaling in Aβ-treated neuronal cells.

Materials and methods

Human brain tissue

Medial temporal gyri from eight patients with AD and seven age- and sex-matched controls were provided by the Netherlands Brain Bank (Additional file 3: Table S1). AD pathological staging was based on the Braak staging system. The hippocampus and cortex from the brains of normal controls and AD patients were analyzed by qRT-PCR, western blotting, synaptosome purification, and immunoprecipitation.

DNA constructs

In summary, we report a novel pathological mechanism of AD, the Aβ-mediated destabilization of the MHC-I-β2M complex and subsequent disruption of NCAM1 signaling. Furthermore, the SCT-mediated restoration of the MHC-I–β2M complex may be a promising therapeutic strategy for restoring synaptic function in AD patients.

Supplementary Information

Because the structural formation of MHC-I-β2M complex is critical for interaction with its functional counterpart, we hypothesized that a conformational change in MHC-I-β2M complex could alter its interactions with unknown synaptic proteins in AD. To identify proteins that interact with neuronal MHC-I, synaptic proteins binding to MHC-I-β2M complexes were co-purified with W6/32 antibody from the synaptosomes of normal human brain and analyzed with a proteomics approach. In addition to detecting several proteins in synaptosomes previously shown to interact with MHC-I-β2M complex, including GRP78, calnexin, and β-COP [–], liquid chromatography-tandem mass spectrometry (LC–MS/MS) identified a 150 kDa protein that interacted with the stable form of MHC-I (Fig. 3A, Additional file 2: Fig. S2A–C, Additional file 3: Table S2). This protein was subsequently identified as NCAM1, a transmembrane glycoprotein that regulates neurite outgrowth, synaptogenesis, and synaptic plasticity [–]. This NCAM1-MHC-I interaction was confirmed by immunoblotting of the same synapse fraction with antibody to NCAM1 (Fig. 3B) and by its coimmunoprecipitation from SH-SY5Y cells expressing HA-tagged NCAM1 (Fig. 3C, D). The NCAM1–MHC-I interaction was further confirmed by a bio-layer interferometry assay using recombinant NCAM1 and MHC-I-β2M complex, with binding affinity of KD of 31.3 nM (Fig. 3E). Therefore, NCAM1 was identified as a novel interactor of MHC-I in human brain synaptosome.

Inhibition of NCAM1 expression and formation of NCAM1–MHC-I complexes in AD
```

</details>

## 40. `f816689c`

**Question.** How did a higher-risk ApoE genetic profile relate to blood-brain barrier biomarkers and to the amyloid 42/40 ratio?

**Reference answer.** It did not affect blood-brain barrier biomarkers, but was associated with lower amyloid 42/40 ratio levels in a dose-dependent manner (H (4) = 9.973, p = 0.041).

**Answer under review.**

> A higher-risk ApoE genetic profile did not affect blood-brain barrier (BBB) biomarkers but was associated with lower levels of the Aβ42/40 ratio in a dose-dependent manner.

<details><summary>Retrieved passages (what the system was shown)</summary>

```
25, p < 0.001), CSF IgG (W = 4951, p < 0.001), and Qalb (W = 4942, p < 0.001). A correlation matrix across all variables in shown in Figure 2.

The Kruskal–Wallis group comparison among different ApoE groups divided by graded risk factor showed that carrying a more high-risk genetic profile did not affect BBB biomarkers but was associated with lower levels of Aβ42/40 ratio in a dose-dependent manner (H (4) = 9.973, p = 0.041), as seen in Figure 3. As there was only one subject with E2/E2 genotype, that subject was excluded from statistical analysis but kept for data visualization purposes.

2.4. Principal Component Analysis

A PCA was then performed to reduce the dimensionality of our dataset and reveal the latent structure of the relationship between the different factors in our data. A five-factor model was able to reflect the data efficiently (PCA model value = 3783, df = 50, p < 0.001), see Figure 4 and Table 3 and Table 4.

The first component (RC1) could reflect sex-related differences in CSF protein (total protein, albumin, IgG) content and Qalb, with males showing higher levels of BBB disruption. The second component (RC2) reflects AD-specific CSF biomarkers, with higher t-tau and p-tau correlating negatively with Aβ42/40 ratio, as expected. The third component (RC3) might reflect the complex interplay between Aβ species, ApoE status, and cognition. The fourth component (RC4) seems to mirror the well-known age effect on serum albumin, with older age being associated with lower serum albumin. The fifth component (RC5) could represent a systemic inflammatory response. To note, RC1, RC2, and RC4 are highly correlated, as seen in Figure 4 and Table 4.

3. Discussion

In light of the recent advent of biomarkers to measure ATN status in blood, a deeper understanding of the impact of BBB dysfunction on AD biomarkers is warranted. Beyond its importance in determining the fine-grain balance between the concentration of AD-specific biomarkers in the blood and in the CSF for diagnostic purposes, this might also extend to a better evaluation of success

brain and plasma Aβ. The underlying hypothesis is that plasma exchange-mediated sequestration of albumin-bound Aβ in plasma would increase the transport of free Aβ from CSF to plasma, thereby decreasing brain Aβ burden. Preliminary results of the Alzheimer’s management by albumin replacement (AMBAR) study show improvements in short-term verbal memory, language fluency, and processing speed in mild–moderate AD patients who underwent plasma exchange, but more evidence is needed to assess its replicability and the feasibility of large-scale implementation. Our data highlight the fact that BBB damage did not differ between patients within the ATN framework, which might be important for patient selection in future clinical trials. However, BBB disruption was associated with lower Aβ40 levels. As Aβ40 has been proposed as a protective factor, being able to dynamically compete with Aβ42 in fibril formation, one might postulate that BBB disruption might lead to lower Aβ40 levels being available to compete with Aβ42 and being potentially detrimental. However, whether this represents a positive or a maladaptive response needs further investigation.

BBB biomarkers were not impacted by the ApoE genotype, but our data support a modulation of the Aβ42/40 ratio with ApoE status. This seems to follow a dose-dependent effect, with ApoE phenotypes at higher risk of developing AD being associated with a lower Aβ42/40 ratio. This result is in line with the previous literature on the association between carrying at least one ApoE4 allele and lower levels of amyloid but not higher levels of tau in the CSF, but extends these findings to participants with different ATN statuses. Moreover, it shows a dose-dependent effect across different genetic subtypes including participants with at least one ApoE2 allele. We were also able to show that ApoE status was not associated with BBB disruption in this sample, which is in line with previous negative findings in ApoE4 positive individuals.

In this study, ageing was only negatively correlated with serum albumin levels and not with Qalb, but the age range was small (60–80 years) when compared to other studies that have investigated the effect of ageing on Qalb across the lifespan, so in our data the variability might not be enough to detect those differences. On the other hand, we were able to confirm that there are sex differences in Qalb, which is in line with

ver R2019a) and JASP (JASP team, 2019). According to the normality of the data, between-group differences within the ATN framework were analysed using either a frequentist one-way analysis of variance (ANOVA) or Kruskal–Wallis H test, followed by Bonferroni post-hoc correction. Based on ApoE genotype, a value was assigned according to the graded risk factor associated to each genotype, with consecutive values given to E2/E2, E2/E3, E3/E3, E2/E4, E3/E4, and E4/E4 according to Reiman et al.. Sex correlations are calculated as male/female ratio, with negative values implying an increased male/female ratio. Correlations between continuous variables were investigated using linear regression. Principal component analysis (PCA) using an oblique promax rotation was used to reduce data dimensionality among multiple variables. Statistical significance was set at p-value < 0.05.

5. Conclusions

Our data showed that BBB dysfunction does not change across different ATN subtypes and that is not correlated with cognitive impairment. However, BBB damage, if measured by Qalb, is associated with low Aβ40 levels, which might potentially have implications for the fine-grain balance between different amyloid species. BBB disruption was not modulated by ApoE status, which, however, showed a dose-dependent effect on the Aβ42/40 ratio. Further studies are needed to replicate these findings including a cohort of cognitively unimpaired individuals and to investigate how blood-based AD-specific biomarkers are impacted by a disruption of the BBB. We hope that this data will highlight the need for further research in this field, which might be crucial for diagnostic and therapeutic purposes.

and concomitant non-Alzheimer’s pathologic change (A+T-N+) and was therefore excluded from subsequent analysis.

Groups were not statistically different in age, sex, MMSE scores, or ApoE status, as shown in Table 1. As expected, the four groups differed in terms of CSF total-tau, p-tau, Aβ42, Aβ40, and the Aβ42/40 ratio (post-hoc analysis in Supplementary Materials Table S1).

We found no difference in any of the BBB biomarkers (protein, serum albumin, CSF albumin, Qalb, serum IgG, CSF IgG, IgG index) among the four groups (Table 2), nor among any group pair after post-hoc Bonferroni correction. Only 1.16% of the patients had abnormal IgG index (>0.7), while 31.2% of our sample had abnormal Qalb, and the percentage was not different among groups.

2.2. Correlation between BBB and AD-Specific Biomarkers

Qalb was correlated with Aβ40 levels (r = −0.190, p = 0.014), but not with Aβ42 or the Aβ42/40 ratio. Patients were then divided according to the integrity of their BBB using the standard age-related Qalb cut-off of eight as having normal Qalb (<8) or high Qalb (>8). We found that the negative correlation between Aβ40 and Qalb was only significant (r = −0.367, p = 0.009) in patients with high Qalb, while in patients with normal Qalb this was not observed (Figure 1). No other significant correlations were found.

2.3. Relationship between BBB Biomarkers, Demographics, and Cognition

MMSE scores were not correlated with the BBB markers studied but were positively correlated with Aβ42 levels, with lower MMSE associated with lower levels of Aβ42 (r = 0.227, p = 0.011). Age was negatively correlated with serum albumin (r = −0.240, p = 0.001), with lower levels of serum albumin seen in elderly individuals. Females had lower CSF proteins (W = 5084, p < 0.001), CSF albumin (W = 48
```

</details>
