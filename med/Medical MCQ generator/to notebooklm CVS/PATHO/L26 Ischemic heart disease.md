นี่คือการดำเนินการเพิ่มคุณค่าทางการแพทย์ (Medical Enrichment) และทำความสะอาดสัญลักษณ์คณิตศาสตร์ (LaTeX Auto-Clean) สำหรับเอกสารสรุปคำบรรยายเรื่อง **Ischemic Heart Disease** 

จากการตรวจสอบเบื้องต้น พบสัญลักษณ์ LaTeX เช่น `$\rightarrow$`, `$\ge$`, `$\le$`, `$\text{SpO}_2 < 90\%$` และ `$>100\ \mu\text{g/L}$` กระจัดกระจายอยู่ในเอกสาร ทางเราได้ดำเนินการแปลงสัญลักษณ์เหล่านี้ให้อยู่ในรูปแบบ **Unicode/Plain Text** ที่อ่านง่ายและเป็นมิตรกับแอปพลิเคชันจดบันทึกทั่วไป (เช่น Notion, Obsidian) เรียบร้อยแล้ว

---

### 📁 ไฟล์ที่สร้างขึ้นใหม่
1. **`notes-clean.md`**: เอกสารต้นฉบับที่ได้รับการทำความสะอาดสัญลักษณ์ LaTeX ทั้งหมดให้เป็น Unicode ที่สวยงาม
2. **`notes-enriched.md`**: เอกสารฉบับสมบูรณ์ที่ผ่านการทำความสะอาด LaTeX และเพิ่มเนื้อหาเชิงลึก 3 ส่วนหลัก (`🧠 กลไกและเหตุผลทางการแพทย์`, `📌 สิ่งที่ต้องรู้ (ภาษาไทย)`, และ `‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์`) ครบถ้วนทั้ง 12 ส่วน (49 หน้าสไลด์)

---

# notes-clean.md

```markdown
## lecture-markdown.md

# 📋 Topic Checklist — สิ่งที่ต้องรู้ทั้งหมด

| หน้า | หัวข้อสไลด์ | สถานะ |
|------|-------------|--------|
| 1    | Ischemic Heart Disease (Title Slide) | ⬜ |
| 2    | Scope | ⬜ |
| 3    | Definition (Ischemia vs Hypoxia) | ⬜ |
| 4    | Ischemic heart disease (IHD) | ⬜ |
| 5    | Pathogenesis of Myocardial Ischemia | ⬜ |
| 6    | Atherosclerosis Progression & Plaque Types | 🖼️ อธิบายภาพแล้ว |
| 7    | Consequences of Myocardial Ischemia | ⬜ |
| 8    | Ischemic Cardiac Pain Radiation | 🖼️ อธิบายภาพแล้ว |
| 9    | Angina Pectoris | ⬜ |
| 10   | Angina Pectoris Classification | ⬜ |
| 11   | Stable (typical) angina | ⬜ |
| 12   | Unstable angina | ⬜ |
| 13   | Prinzmetal's (variant) | ⬜ |
| 14   | Myocardial Infarction (MI) Overview | ⬜ |
| 15   | Pathogenesis of Acute MI | ⬜ |
| 16   | Sequence of Events in Typical MI (Part 1) | ⬜ |
| 17   | Sequence of Events in Typical MI (Part 2) | ⬜ |
| 18   | Myocardial Infarction Type 1 vs Type 2 | 🖼️ อธิบายภาพแล้ว |
| 19   | Atherosclerosis Progression Diagram (Robbins) | 🖼️ อธิบายภาพแล้ว |
| 20   | Coronary Artery Pathology in Ischemic Heart Disease | ⬜ |
| 21   | Other Mechanisms Involved in MI | ⬜ |
| 22   | Atherosclerosis, Clot, and Spasm Diagrams | 🖼️ อธิบายภาพแล้ว |
| 23   | Frequencies of Critical Narrowing in Coronary Arteries | 🖼️ อธิบายภาพแล้ว |
| 24   | Key Events in Ischemic Cardiac Myocytes & Necrosis Progression | 🖼️ อธิบายภาพแล้ว |
| 25   | Approximate Time of Onset of Key Events (Table) | ⬜ |
| 26   | Pattern of Infarction | ⬜ |
| 27   | Distribution of Myocardial Ischemic Necrosis | 🖼️ อธิบายภาพแล้ว |
| 28   | Table 12-5 Evolution of Morphologic Changes in MI | ⬜ |
| 29   | Figure 12-13 Gross Pathology of Acute MI (TTC Stain) | 🖼️ อธิบายภาพแล้ว |
| 30   | Figure 12-14 Microscopic Features of MI and Repair | 🖼️ อธิบายภาพแล้ว |
| 31   | Biochemical Changes & Salvageable Myocardium Graphs | 🖼️ อธิบายภาพแล้ว |
| 32   | Biomarkers of Myocardial Infarction (Troponin) | 🖼️ อธิบายภาพแล้ว |
| 33   | Acute Coronary Syndrome (ACS) Diagnostic Flowchart | 🖼️ อธิบายภาพแล้ว |
| 34   | Pre-hospital Assessment and Management (AHA Guideline) | 🖼️ อธิบายภาพแล้ว |
| 35   | Thai Acute Coronary Syndromes Guidelines 2020 | 🖼️ อธิบายภาพแล้ว |
| 36   | Complications of Myocardial Infarction Flowchart | 🖼️ อธิบายภาพแล้ว |
| 37   | Timeline of MI Complications | 🖼️ อธิบายภาพแล้ว |
| 38   | Figure 12-18 Gross Pathology of MI Complications | 🖼️ อธิบายภาพแล้ว |
| 39   | Sudden Cardiac Death (SCD) Overview | ⬜ |
| 40   | Non-atherosclerotic Causes of SCD | ⬜ |
| 41   | Mechanism of SCD & Implantable Cardioverter Defibrillator | ⬜ |
| 42   | Figure 12-19 Causes and Outcomes of Ischemic Heart Disease | 🖼️ อธิบายภาพแล้ว |
| 43   | Treatment: PCI and CABG Diagrams | 🖼️ อธิบายภาพแล้ว |
| 44   | Immediate Care & Reperfusion Therapy | ⬜ |
| 45   | Management of Ischemic Heart Disease (Lifestyle) | ⬜ |
| 46   | Figure 7 Recommended Nutrition | 🖼️ อธิบายภาพแล้ว |
| 47   | Chronic Ischemic Heart Disease (CIHD) | ⬜ |
| 48   | Clinical Diagnosis of CIHD | ⬜ |
| 49   | End Slide (Kitten Image) | 🖼️ อธิบายภาพแล้ว |

---

## Section 1: Introduction & Definitions — หน้า 1–4

> 📍 **ตำแหน่งในเอกสาร:** หน้า 1–4

### เนื้อหาจากสไลด์

#### หน้า 1: Title Slide
*   **Ischemic Heart Disease**
*   Chaiwat Aphivatanasiri, M.D.
    *   Department of Pathology,
    *   Faculty of Medicine,
    *   Khon Kaen University

#### หน้า 2: Scope
*   **Definition**
*   **Pathogenesis**
    *   Atherosclerosis
*   **Ischemic heart disease**
    *   Myocardial infarction (MI)
    *   Angina pectoris
    *   Sudden cardiac death
    *   Chronic IHD with heart failure
*   **Management**

#### หน้า 3: Definition
*   **"Ischemia"**
    *   A situation where there is not enough oxygen reaching the cells of the body.
    *   An insufficient amount of blood.
    *   `Decrease perfusion` → `Hypoxia (Hypoperfusion)`
*   **"Hypoxia"** means reduced level of oxygen at the cell level.

#### หน้า 4: Ischemic heart disease (IHD)
*   Also known as **Coronary Artery Disease / Coronary Heart Disease**
*   Represents a group of related syndromes resulting from myocardial ischemia.
*   An imbalance between myocardial supply (perfusion) and cardiac demand for oxygenated blood.
*   Ischemia not only limits tissue oxygenation but also reduces the availability of nutrients and the removal of metabolic wastes.

---

## Section 2: Pathogenesis of Atherosclerosis & Plaque Dynamics — หน้า 5–6

> 📍 **ตำแหน่งในเอกสาร:** หน้า 5–6

### เนื้อหาจากสไลด์

#### หน้า 5: Pathogenesis
*   In more than 90% of cases, myocardial ischemia results from reduced blood flow due to obstructive **atherosclerotic lesions** in the epicardial coronary arteries.
*   It may be **chronic**, a narrowing of the coronary artery over time, and a limitation of the blood supply to part of the muscle.
*   Or it can be **acute**, resulting from a sudden rupture of a plaque and formation of a thrombus or blood clot.

#### หน้า 6: Atherosclerosis Progression & Plaque Types
*(สไลด์แสดงแผนภาพการดำเนินไปของโรค Atherosclerosis และภาพทางจุลพยาธิวิทยาของคราบไขมันชนิดต่างๆ)*

---

## Section 3: Consequences of Myocardial Ischemia & Angina Pectoris — หน้า 7–13

> 📍 **ตำแหน่งในเอกสาร:** หน้า 7–13

### เนื้อหาจากสไลด์

#### หน้า 7: Consequences of Myocardial Ischemia
*   **Myocardial infarction (MI)**, where ischemia causes frank cardiac necrosis.
*   **Angina pectoris ("chest pain")**, where ischemia is not severe enough to cause infarction, but the symptoms nevertheless portend infarction risk.
*   **Chronic IHD with heart failure**
*   **Sudden cardiac death (SCD)**

#### หน้า 8: Ischemic Cardiac Pain
*   **A. Common:** The pain most often radiates to the ulnar side of the left arm.
*   **B. Uncommon:** Less often the pain radiates to the right side, the neck, and the face, or to the dorsal side of the chest.

#### หน้า 9: Angina Pectoris
*   At least **70% occlusion** of coronary artery resulting in pain.
*   Usually brought on by physical exertion as the heart is trying to pump blood to the muscles, it requires more blood that is not available due to the blockage of the coronary artery/arteries.
*   Is self-limiting → usually stops when exertion is ceased.

#### หน้า 10: Angina Pectoris Classification
*   **Stable (typical)**
*   **Unstable (crescendo)**
*   **Prinzmetal's (variant)**

#### หน้า 11: Stable (typical) angina
*   Recurrent attacks of substernal or precordial chest discomfort caused by transient (**15s - 15 mins**) myocardial ischemia.
*   Imbalance in coronary perfusion relative to myocardial demand (physical activity, emotional excitement, psychological stress).
*   Usually relieved by rest or administering vasodilators (e.g., Nitroglycerin).
*   Myocardial ischemia that is insufficient to induce myocyte necrosis.

#### หน้า 12: Unstable angina
*   Increasingly frequent, prolonged (**>20 mins**), or severe angina or chest discomfort progressing at lower levels of physical activity or even occurring at rest.
*   Caused by the disruption of an atherosclerotic plaque.
*   **50% of patients** have evidence of myocardial infarction.

#### หน้า 13: Prinzmetal's (variant)
*   Rare, representing about two out of 100 cases of angina, and usually occurs in younger patients.
*   **Causes:** a spasm in the coronary arteries.
*   The coronary arteries can spasm as a result of: exposure to cold weather, stress, medicines, smoking, cocaine use.
*   **Symptoms:** pain or discomfort: usually occurs while resting and during the night or early morning hours.
*   Prinzmetal angina generally responds promptly to vasodilators, such as nitroglycerin and calcium channel blockers.

---

## Section 4: Myocardial Infarction (MI) Overview & Pathogenesis — หน้า 14–22

> 📍 **ตำแหน่งในเอกสาร:** หน้า 14–22

### เนื้อหาจากสไลด์

#### หน้า 14: Myocardial Infarction (MI)
*   MI, also known as **"heart attack,"** is the death of cardiac muscle resulting from ischemia.
*   Partial or total occlusion of one or more of the coronary arteries due to an atheroma, thrombus or emboli resulting in cell death (infarction) of the heart muscle.
*   250,000 deaths per year.
*   **30% mortality** within the first 2 hours.
*   **45 Minutes of Ischemia:** Cardiac muscle death occurs.

#### หน้า 15: Pathogenesis of Acute MI
*   Acute MI results from a dynamic interaction among several or all the following:
    *   Coronary atherosclerosis
    *   Acute atheromatous plaque change (such as rupture)
    *   Superimposed platelet activation
    *   Thrombosis
    *   Vasospasm
*   → resulting in an **occlusive intracoronary thrombus** overlying a disrupted plaque.

#### หน้า 16: Sequence of Events in Typical MI (Part 1)
*   The following sequence of events can be proposed:
    *   The initial event is a sudden change in the morphology of an atheromatous plaque, that is, **disruption**—manifest as intraplaque hemorrhage, erosion or ulceration, or rupture or fissuring.
    *   Exposed to subendothelial collagen and necrotic plaque contents, platelets undergo **adhesion, aggregation, activation**, and release of potent aggregators including thromboxane A2, serotonin, and platelet factors 3 and 4.

#### หน้า 17: Sequence of Events in Typical MI (Part 2)
*   **Vasospasm** is stimulated by platelet aggregation and the release of mediators.
*   Other mediators activate the **extrinsic pathway of coagulation**, adding to the bulk of the thrombus.
*   Frequently within minutes, the thrombus evolves to **completely occlude** the lumen of the coronary vessel.

#### หน้า 18: Myocardial Infarction Type 1 vs Type 2
*(สไลด์แสดงภาพเปรียบเทียบกลไกการเกิด MI Type 1 และ Type 2)*

#### หน้า 19: Atherosclerosis Progression Diagram (Robbins)
*(สไลด์แสดงแผนภาพการดำเนินโรคของ Atherosclerosis จากตำรา Robbins Basic Pathology)*

#### หน้า 20: Coronary Artery Pathology in Ischemic Heart Disease
| Syndrome | Stenosis | Plaque Disruption | Plaque-Associated Thrombus |
| :--- | :--- | :--- | :--- |
| **Stable angina** | >75% | No | No |
| **Unstable angina** | Variable | Frequent | Non-occlusive, often with thrombo-emboli |
| **Transmural MI** | Variable | Frequent | Occlusive |
| **Subendocardial MI** | Variable | Variable | Widely variable, may be absent, partial/complete, or lysed |
| **Sudden death** | Usually severe | Frequent | Often small platelet aggregates or thrombi and/or thrombo-emboli |

#### หน้า 21: Other Mechanisms Involved in MI
*   **Vasospasm:** with or without coronary atherosclerosis, perhaps in association with platelet aggregation (sometimes related to cocaine abuse).
*   **Emboli:** association with atrial fibrillation, a left-sided mural thrombus or vegetative endocarditis; or paradoxical emboli from the right side of the heart or the peripheral veins which cross to the systemic circulation, through a patent foramen ovale, causing coronary occlusion.
*   **Unexplained:** cases without detectable coronary atherosclerosis and thrombosis may be caused by diseases of small intramural coronary vessels, such as:
    *   Vasculitis
    *   Hematologic abnormalities such as hemoglobinopathies
    *   Amyloid deposition in vascular walls
    *   Other unusual disorders, such as vascular dissection.

#### หน้า 22: Atherosclerosis, Clot, and Spasm Diagrams
*(สไลด์แสดงภาพวาดเปรียบเทียบพยาธิสภาพ 3 รูปแบบ: Atherosclerosis with blood clot, Atherosclerosis เดี่ยวๆ, และ Spasm)*

---

## Section 5: Coronary Anatomy, Myocyte Injury Timeline & Patterns of Infarction — หน้า 23–27

> 📍 **ตำแหน่งในเอกสาร:** หน้า 23–27

### เนื้อหาจากสไลด์

#### หน้า 23: Frequencies of Critical Narrowing in Coronary Arteries
*   The frequencies of critical narrowing (and thrombosis) of each of the three main arterial trunks and the corresponding sites of myocardial lesions resulting in infarction (in the typical right dominant heart) are as follows:
    *   **40-50%:** **Anterior Descending Branch of Left Coronary Artery (LAD)**
        *   Anterior wall of left ventricle
        *   Front 2/3 of septum, including the bundle branches
    *   **30-40%:** **Right Coronary Artery (RCA)**
        *   Inferior wall of left ventricle (in most people)
        *   Right ventricle
        *   Right atrium, including SA and AV nodes (most people)
    *   **15-20%:** **Circumflex Branch of Left Coronary Artery (LCX)**
        *   High lateral wall of LV
        *   Some of posterior wall (varies in people)

#### หน้า 24-25: Key Events in Ischemic Cardiac Myocytes
*   **Table 12-4: Approximate Time of Onset of Key Events in Ischemic Cardiac Myocytes**
| Feature | Time |
| :--- | :--- |
| **Onset of ATP depletion** | Seconds |
| **Loss of contractility** | <2 minutes |
| **ATP reduced to 50% of normal** | 10 minutes |
| **ATP reduced to 10% of normal** | 40 minutes |
| **Irreversible cell injury** | 20-40 minutes |
| **Microvascular injury** | >1 hour |

#### หน้า 26: Pattern of Infarction
*   **Transmural Infarction:** Ischemic necrosis involves the full or nearly full thickness of the ventricular wall.
*   **Subendocardial (non-transmural) Infarction:** Ischemic necrosis limited to the inner one-third or at most one-half of the ventricular wall.
*   **Multifocal microinfarction:** Involving only smaller intramural vessels, such as microembolization, vasculitis, or vascular spasm.

#### หน้า 27: Distribution of Myocardial Ischemic Necrosis
*(สไลด์แสดงแผนภาพเปรียบเทียบพยาธิสภาพการตายของกล้ามเนื้อหัวใจแบบ Transmural และ Non-transmural)*

---

## Section 6: Pathology of MI: Morphologic Changes & Histology — หน้า 28–30

> 📍 **ตำแหน่งในเอกสาร:** หน้า 28–30

### เนื้อหาจากสไลด์

#### หน้า 28: Evolution of Morphologic Changes in Myocardial Infarction
*   **Table 12-5: Evolution of Morphologic Changes in Myocardial Infarction**
| Time | Gross Features | Light Microscope | Electron Microscope |
| :--- | :--- | :--- | :--- |
| **Reversible Injury** | | | |
| 0 - 1/2 hr | None | None | Relaxation of myofibrils; glycogen loss; mitochondrial swelling |
| **Irreversible Injury** | | | |
| 1/2 - 4 hr | None | Usually none; variable waviness of fibers at border | Sarcolemmal disruption; mitochondrial amorphous densities |
| 4 - 12 hr | Dark mottling (occasional) | Early coagulation necrosis; edema; hemorrhage | |
| 12 - 24 hr | Dark mottling | Ongoing coagulation necrosis; pyknosis of nuclei; myocyte hypereosinophilia; marginal contraction band necrosis; early neutrophilic infiltrate | |
| 1 - 3 days | Mottling with yellow-tan infarct center | Coagulation necrosis, with loss of nuclei and striations; brisk interstitial infiltrate of neutrophils | |
| 3 - 7 days | Hyperemic border; central yellow-tan softening | Beginning disintegration of dead myofibers, with dying neutrophils; early phagocytosis of dead cells by macrophages at infarct border | |
| 7 - 10 days | Maximally yellow-tan and soft, with depressed red-tan margins | Well-developed phagocytosis of dead cells; granulation tissue at margins | |
| 10 - 14 days | Red-gray depressed infarct borders | Well-established granulation tissue with new blood vessels and collagen deposition | |
| 2 - 8 wk | Gray-white scar, progressive from border toward core of infarct | Increased collagen deposition, with decreased cellularity | |
| >2 mo | Scarring complete | Dense collagenous scar | |

#### หน้า 29: Gross Pathology of Acute MI
*(สไลด์แสดงภาพตัดขวางของหัวใจที่ย้อมด้วยสารเคมีพิเศษเพื่อตรวจหาเนื้อตาย)*

#### หน้า 30: Microscopic Features of MI and Repair
*(สไลด์แสดงภาพจุลพยาธิวิทยาของกล้ามเนื้อหัวใจในระยะต่างๆ ตั้งแต่ 1 วัน จนถึงกลายเป็นแผลเป็น)*

---

## Section 7: Pathophysiology, Biomarkers & Diagnosis of ACS — หน้า 31–33

> 📍 **ตำแหน่งในเอกสาร:** หน้า 31–33

### เนื้อหาจากสไลด์

#### หน้า 31: Biochemical Changes & Salvageable Myocardium Graphs
*(สไลด์แสดงกราฟความสัมพันธ์ระหว่างสารเคมีในเซลล์กับเวลา และสัดส่วนเนื้อหัวใจที่ช่วยชีวิตได้)*

#### หน้า 32: Biomarkers of Myocardial Infarction (Troponin)
*   **1. Onset of myocardial infarction**
*   **2. Plasma membrane of necrotic myocytes becomes leaky**
*   **3. Troponin leaks out of cell into circulation**
*   **4. Biomarker for diagnosis of myocardial infarction**
*   **Troponin Concentration Ranges:**
    *   `0.001 µg/L` → Healthy
    *   `0.01 µg/L` → Stable Angina, Chronic heart failure
    *   `0.1 µg/L` → Micro MI, Myocarditis, Acute heart failure
    *   `1 µg/L` → Small MI, Myocarditis, Pulmonary embolism
    *   `10 µg/L` → Medium sized MI, Severe myocarditis
    *   `100 µg/L` → Large MI
*   **Symptoms:** Chest Pain, Increase in level of cardiac biomarkers
*   **MI detection:** ECG, Cardiac biomarker detection

#### หน้า 33: Acute Coronary Syndrome (ACS) Diagnostic Flowchart
*(สไลด์แสดงแผนผังการวินิจฉัยแยกโรคในกลุ่มอาการโคโรนารีเฉียบพลัน)*

---

## Section 8: Pre-hospital Assessment, Thai ACS Guidelines & Reperfusion — หน้า 34–35

> 📍 **ตำแหน่งในเอกสาร:** หน้า 34–35

### เนื้อหาจากสไลด์

#### หน้า 34: Pre-hospital Assessment and Management (AHA Guideline)
*   **Pre-hospital Assessment and Management Considerations for Suspected ACS**
*   **Suspected ACS** → Evaluation by Emergency Medical Services → **12-Lead ECG** (Within 10 minutes of First Medical Contact).
*   **STEMI:** Immediate transfer to PCI-capable hospital. Goal of First Medical Contact to Device Time **≤ 90 minutes**.
*   **Non-Diagnostic For STEMI:** Transport to Local Emergency Department. Further in-hospital assessment of confirmed or suspected ACS.
*   **Serial ECGs:** To detect potential ischemic changes, especially if clinical suspicion for ACS remains high.
*   **In patients with STEMI managed with primary PCI:**
    *   Each **30 minute delay** is associated with a **7.5% relative risk** of 1-year death.

#### หน้า 35: Thai Acute Coronary Syndromes Guidelines 2020
*   **แนวทางปฏิบัติการดูแลรักษาผู้ป่วยภาวะหัวใจขาดเลือดเฉียบพลัน พ.ศ. 2563**
*   **First medical contact (FMC)** หมายถึงผู้เห็นเหตุการณ์คนแรก ณ จุดแรกที่พบผู้ป่วย
*   **STEMI diagnosis** ต้องทำภายใน **<10 นาที**
*   **Reperfusion Strategy Decision:**
    *   หากส่งตัวไปถึงโรงพยาบาลที่ทำ PCI ได้ภายใน **≤ 120 นาที** → เลือก **Primary PCI** (Reperfusion strategy: Wire Crossing)
    *   หากใช้เวลาส่งตัวมากกว่า **> 120 นาที** → เลือก **Fibrinolysis strategy** (Reperfusion strategy: Needle) ทันที

---

## Section 9: Complications of Myocardial Infarction — หน้า 36–38

> 📍 **ตำแหน่งในเอกสาร:** หน้า 36–38

### เนื้อหาจากสไลด์

#### หน้า 36: Complications of Myocardial Infarction Flowchart
*   **Myocardial Infarction Complications:**
    *   **Impaired contractility**
        *   → Ventricular thrombus → **Stroke (embolism)**
        *   → Hypotension → decrease coronary perfusion → increase ischemia → **Cardiogenic shock**
        *   → **Congestive heart failure**
    *   **Tissue necrosis**
        *   → Papillary muscle infarction → Mitral regurgitation → **Congestive heart failure**
        *   → Ventricular wall rupture → **Cardiac tamponade**
    *   **Electrical instability**
        *   → **Arrhythmias**
    *   **Pericardial inflammation**
        *   → **Pericarditis**

#### หน้า 37: Timeline of MI Complications
*   **Acute MI** → Timeline of complications:
    *   **< 4 hours:** Ventricular arrhythmias (ventricular fibrillation or tachycardia) - Primary: due to ischemia.
    *   **< 24 hours:** Bradyarrhythmias / heart block. Common, especially with inferior myocardial infarction. Often resolve spontaneously if onset <24 h.
    *   **3 days:**
        *   *Cardiogenic shock:* Strongly dependent on infarct size; 5-6% of patients with STEMI.
        *   *Stroke:* Thromboembolic from PCI or hemorrhagic from antithrombotic therapy. Long-term risk in large anterior infarct, left ventricular aneurysm, or reduced left ventricular ejection fraction.
        *   *Ischemic MR / papillary muscle rupture:* Posterior papillary muscle most often; supplied by dominant artery. Characteristic murmur of MR may be absent.
        *   *Ventricular septal rupture:* Most common with anterior myocardial infarction. Holosystolic murmur at LSB (Left Sternal Border).
    *   **2 weeks:**
        *   *LV free wall rupture:* Persistent STE, upright T-waves, reversal of initially inverted T-waves. >50% mortality even with surgery.
        *   *Pericarditis (Dressler syndrome):* Autoimmune reaction; more common in large infarcts. Persistent STE, PR depression, may have a friction rub.

#### หน้า 38: Figure 12-18 Gross Pathology of MI Complications
*(สไลด์แสดงภาพถ่ายหัวใจจริงที่เกิดภาวะแทรกซ้อนรุนแรงรูปแบบต่างๆ)*

---

## Section 10: Sudden Cardiac Death (SCD) — หน้า 39–42

> 📍 **ตำแหน่งในเอกสาร:** หน้า 39–42

### เนื้อหาจากสไลด์

#### หน้า 39: Sudden Cardiac Death (SCD)
*   Defined as **unexpected death from cardiac causes** early after symptom onset (usually within 1 hour) or without the onset of symptoms.
*   Is also known as a **"Massive Heart Attack"** in which the heart converts from sinus rhythm to ventricular fibrillation.

#### หน้า 40: Non-atherosclerotic Causes of SCD
*   Non-atherosclerotic causes of SCD become increasingly probable in decreasing age patient:
    *   Congenital structural or coronary arterial abnormalities
    *   Aortic valve stenosis
    *   Mitral valve prolapse
    *   Myocarditis
    *   Dilated or hypertrophic cardiomyopathy
    *   Pulmonary hypertension
    *   Hereditary or acquired abnormalities of the cardiac conduction system
    *   Isolated hypertrophy, hypertensive or unknown cause.

#### หน้า 41: Mechanism of SCD
*   The mechanism of SCD is most often a **lethal arrhythmia** (e.g., asystole, ventricular fibrillation).
*   **Fatal arrhythmia** is triggered by electrical irritability of myocardium that may be distant from the conduction system, induced by ischemia.
*   The prognosis of patients vulnerable to SCD, especially those with chronic IHD, is markedly improved by implantation of an **automatic cardioverter defibrillator (ICD)**, which senses and electrically counteracts an episode of ventricular fibrillation.

#### หน้า 42: Figure 12-19 Causes and Outcomes of Ischemic Heart Disease
*(สไลด์แสดงแผนผังความเชื่อมโยงระหว่างโรคหลอดเลือดหัวใจ, กล้ามเนื้อหัวใจตาย, หัวใจล้มเหลว และการเสียชีวิตเฉียบพลัน)*

---

## Section 11: Treatment & Management of Ischemic Heart Disease — หน้า 43–46

> 📍 **ตำแหน่งในเอกสาร:** หน้า 43–46

### เนื้อหาจากสไลด์

#### หน้า 43: Treatment: PCI and CABG Diagrams
*(สไลด์แสดงภาพขั้นตอนการทำสวนหัวใจขยายหลอดเลือด และการผ่าตัดบายพาสหลอดเลือดหัวใจ)*

#### หน้า 44: Immediate Care & Reperfusion Therapy
*   **Immediate Care:**
    *   **Aspirin administration:** Aspirin is given as soon as possible unless contraindicated, to reduce blood clotting.
    *   **Nitroglycerin (nitrate):** Used for chest pain relief unless contraindicated.
    *   **Oxygen:** Administered if there are signs of hypoxia or respiratory distress.
    *   **Analgesia:** Morphine is used to manage severe chest pain.
    *   **Antiplatelet therapy:** A P2Y12 inhibitor is often given in addition to aspirin.
    *   **Anticoagulation:** Medications such as heparin are used to prevent further clotting.
*   **Reperfusion Therapy (for STEMI):**
    *   **1. Percutaneous Coronary Intervention (PCI):** Preferred if it can be performed within 90 minutes of first medical contact.
    *   **2. Thrombolysis:** Considered if PCI is not available within the recommended time frame.

#### หน้า 45: Management of Ischemic Heart Disease (Lifestyle)
*   **Management of Ischemic Heart Disease:**
    *   **Lifestyle:**
        *   Diet
        *   Exercise Preventive treatment
        *   Low-fat, low-cholesterol diet
        *   Cessation of smoking

#### หน้า 46: Figure 7 Recommended Nutrition
*(สไลด์แสดงภาพคำแนะนำการเลือกรับประทานอาหารเพื่อสุขภาพหัวใจ)*

---

## Section 12: Chronic Ischemic Heart Disease (CIHD) — หน้า 47–49

> 📍 **ตำแหน่งในเอกสาร:** หน้า 47–49

### เนื้อหาจากสไลด์

#### หน้า 47: Chronic Ischemic Heart Disease (CIHD)
*   Is used here to describe the cardiac findings in patients, often but not exclusively elderly, who develop **progressive heart failure** as a consequence of ischemic myocardial damage.
*   The term **ischemic cardiomyopathy** is often used by clinicians to describe Chronic ischemic heart disease (CIHD).

#### หน้า 48: Clinical Diagnosis of CIHD
*   Is made by the **insidious onset of CHF** (Congestive Heart Failure) in patients who have had past episodes of MI or anginal attacks.
*   In some individuals, however, progressive myocardial damage is entirely **silent**, and heart failure is the first indication of CIHD.

#### หน้า 49: End Slide
*   **END**
*(สไลด์แสดงภาพลูกแมวสีส้มตากลมโตเพื่อจบการนำเสนอ)*
```

---

# notes-enriched.md

```markdown
## lecture-markdown.md

# 📋 Topic Checklist — สิ่งที่ต้องรู้ทั้งหมด

| หน้า | หัวข้อสไลด์ | สถานะ |
|------|-------------|--------|
| 1    | Ischemic Heart Disease (Title Slide) | ✅ แปลงเนื้อหาแล้ว |
| 2    | Scope | ✅ แปลงเนื้อหาแล้ว |
| 3    | Definition (Ischemia vs Hypoxia) | ✅ แปลงเนื้อหาแล้ว |
| 4    | Ischemic heart disease (IHD) | ✅ แปลงเนื้อหาแล้ว |
| 5    | Pathogenesis of Myocardial Ischemia | ✅ แปลงเนื้อหาแล้ว |
| 6    | Atherosclerosis Progression & Plaque Types | 🖼️ อธิบายภาพแล้ว |
| 7    | Consequences of Myocardial Ischemia | ✅ แปลงเนื้อหาแล้ว |
| 8    | Ischemic Cardiac Pain Radiation | 🖼️ อธิบายภาพแล้ว |
| 9    | Angina Pectoris | ✅ แปลงเนื้อหาแล้ว |
| 10   | Angina Pectoris Classification | ✅ แปลงเนื้อหาแล้ว |
| 11   | Stable (typical) angina | ✅ แปลงเนื้อหาแล้ว |
| 12   | Unstable angina | ✅ แปลงเนื้อหาแล้ว |
| 13   | Prinzmetal's (variant) | ✅ แปลงเนื้อหาแล้ว |
| 14   | Myocardial Infarction (MI) Overview | ✅ แปลงเนื้อหาแล้ว |
| 15   | Pathogenesis of Acute MI | ✅ แปลงเนื้อหาแล้ว |
| 16   | Sequence of Events in Typical MI (Part 1) | ✅ แปลงเนื้อหาแล้ว |
| 17   | Sequence of Events in Typical MI (Part 2) | ✅ แปลงเนื้อหาแล้ว |
| 18   | Myocardial Infarction Type 1 vs Type 2 | 🖼️ อธิบายภาพแล้ว |
| 19   | Atherosclerosis Progression Diagram (Robbins) | 🖼️ อธิบายภาพแล้ว |
| 20   | Coronary Artery Pathology in Ischemic Heart Disease | ✅ แปลงเนื้อหาแล้ว |
| 21   | Other Mechanisms Involved in MI | ✅ แปลงเนื้อหาแล้ว |
| 22   | Atherosclerosis, Clot, and Spasm Diagrams | 🖼️ อธิบายภาพแล้ว |
| 23   | Frequencies of Critical Narrowing in Coronary Arteries | 🖼️ อธิบายภาพแล้ว |
| 24   | Key Events in Ischemic Cardiac Myocytes & Necrosis Progression | 🖼️ อธิบายภาพแล้ว |
| 25   | Approximate Time of Onset of Key Events (Table) | ✅ แปลงเนื้อหาแล้ว |
| 26   | Pattern of Infarction | ✅ แปลงเนื้อหาแล้ว |
| 27   | Distribution of Myocardial Ischemic Necrosis | 🖼️ อธิบายภาพแล้ว |
| 28   | Table 12-5 Evolution of Morphologic Changes in MI | ✅ แปลงเนื้อหาแล้ว |
| 29   | Figure 12-13 Gross Pathology of Acute MI (TTC Stain) | 🖼️ อธิบายภาพแล้ว |
| 30   | Figure 12-14 Microscopic Features of MI and Repair | 🖼️ อธิบายภาพแล้ว |
| 31   | Biochemical Changes & Salvageable Myocardium Graphs | 🖼️ อธิบายภาพแล้ว |
| 32   | Biomarkers of Myocardial Infarction (Troponin) | 🖼️ อธิบายภาพแล้ว |
| 33   | Acute Coronary Syndrome (ACS) Diagnostic Flowchart | 🖼️ อธิบายภาพแล้ว |
| 34   | Pre-hospital Assessment and Management (AHA Guideline) | 🖼️ อธิบายภาพแล้ว |
| 35   | Thai Acute Coronary Syndromes Guidelines 2020 | 🖼️ อธิบายภาพแล้ว |
| 36   | Complications of Myocardial Infarction Flowchart | 🖼️ อธิบายภาพแล้ว |
| 37   | Timeline of MI Complications | 🖼️ อธิบายภาพแล้ว |
| 38   | Figure 12-18 Gross Pathology of MI Complications | 🖼️ อธิบายภาพแล้ว |
| 39   | Sudden Cardiac Death (SCD) Overview | ✅ แปลงเนื้อหาแล้ว |
| 40   | Non-atherosclerotic Causes of SCD | ✅ แปลงเนื้อหาแล้ว |
| 41   | Mechanism of SCD & Implantable Cardioverter Defibrillator | ✅ แปลงเนื้อหาแล้ว |
| 42   | Figure 12-19 Causes and Outcomes of Ischemic Heart Disease | 🖼️ อธิบายภาพแล้ว |
| 43   | Treatment: PCI and CABG Diagrams | 🖼️ อธิบายภาพแล้ว |
| 44   | Immediate Care & Reperfusion Therapy | ✅ แปลงเนื้อหาแล้ว |
| 45   | Management of Ischemic Heart Disease (Lifestyle) | ✅ แปลงเนื้อหาแล้ว |
| 46   | Figure 7 Recommended Nutrition | 🖼️ อธิบายภาพแล้ว |
| 47   | Chronic Ischemic Heart Disease (CIHD) | ✅ แปลงเนื้อหาแล้ว |
| 48   | Clinical Diagnosis of CIHD | ✅ แปลงเนื้อหาแล้ว |
| 49   | End Slide (Kitten Image) | 🖼️ อธิบายภาพแล้ว |

---

## Section 1: Introduction & Definitions — หน้า 1–4

> 📍 **ตำแหน่งในเอกสาร:** หน้า 1–4

### เนื้อหาจากสไลด์

#### หน้า 1: Title Slide
*   **Ischemic Heart Disease**
*   Chaiwat Aphivatanasiri, M.D.
    *   Department of Pathology,
    *   Faculty of Medicine,
    *   Khon Kaen University

#### หน้า 2: Scope
*   **Definition**
*   **Pathogenesis**
    *   Atherosclerosis
*   **Ischemic heart disease**
    *   Myocardial infarction (MI)
    *   Angina pectoris
    *   Sudden cardiac death
    *   Chronic IHD with heart failure
*   **Management**

#### หน้า 3: Definition
*   **"Ischemia"**
    *   A situation where there is not enough oxygen reaching the cells of the body.
    *   An insufficient amount of blood.
    *   `Decrease perfusion` → `Hypoxia (Hypoperfusion)`
*   **"Hypoxia"** means reduced level of oxygen at the cell level.

#### หน้า 4: Ischemic heart disease (IHD)
*   Also known as **Coronary Artery Disease / Coronary Heart Disease**
*   Represents a group of related syndromes resulting from myocardial ischemia.
*   An imbalance between myocardial supply (perfusion) and cardiac demand for oxygenated blood.
*   Ischemia not only limits tissue oxygenation but also reduces the availability of nutrients and the removal of metabolic wastes.

### 🧠 กลไกและเหตุผลทางการแพทย์
1. **ความแตกต่างระหว่าง Ischemia และ Hypoxia**: 
    * **Hypoxia** คือภาวะที่เนื้อเยื่อขาดออกซิเจนเพียงอย่างเดียว (เช่น จากภาวะอนีเมีย หรือการขึ้นที่สูง) แต่ยังมีเลือดมาเลี้ยงเพื่อนำสารอาหารมาส่งและนำของเสียกลับได้ตามปกติ
    * **Ischemia** เกิดจากภาวะ **Hypoperfusion** (เลือดมาเลี้ยงลดลง) ส่งผลให้เนื้อเยื่อขาดทั้งออกซิเจนและสารอาหาร (เช่น กลูโคส) อีกทั้งยังเกิดการสะสมของเสียจากการเผาผลาญ (Metabolic wastes เช่น แล็คเตต และไฮโดรเจนไอออน) ซึ่งส่งผลเสียต่อเซลล์รุนแรงกว่าภาวะ Hypoxia เดี่ยวๆ
2. **กลไกการเกิด Imbalance (Supply vs Demand)**:
    * **Myocardial Oxygen Supply** ขึ้นอยู่กับ: Coronary artery blood flow (ซึ่งถูกจำกัดโดยการตีบของหลอดเลือด), ออกซิเจนในเลือด (Oxygen carrying capacity), และ Diastolic perfusion pressure
    * **Myocardial Oxygen Demand** ขึ้นอยู่กับ: Heart rate, Myocardial contractility, และ Myocardial wall tension (ขึ้นกับ Preload และ Afterload)
    * เมื่อเกิดความไม่สมดุล (เช่น ออกกำลังกายทำให้ Demand เพิ่มขึ้น แต่หลอดเลือดตีบทำให้ Supply เพิ่มตามไม่ได้) จะกระตุ้นให้เกิดภาวะ Ischemia ทันที

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* **Ischemia** คือภาวะที่เนื้อเยื่อขาดเลือดไปเลี้ยง ส่งผลให้ขาดทั้งออกซิเจน สารอาหาร และเกิดการคั่งของของเสีย ซึ่งรุนแรงกว่า **Hypoxia** ที่เป็นการขาดออกซิเจนเพียงอย่างเดียว
* **Ischemic Heart Disease (IHD)** หรือโรคหัวใจขาดเลือด มีสาเหตุหลักมาจากความไม่สมดุลระหว่างความต้องการออกซิเจนของกล้ามเนื้อหัวใจ (Demand) และปริมาณเลือดที่นำออกซิเจนมาเลี้ยงหัวใจ (Supply)

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
✅ ข้อมูลสอดคล้องกับแหล่งอ้างอิงทางการแพทย์มาตรฐาน (เช่น *AHA/ACC Guidelines*)

---

## Section 2: Pathogenesis of Atherosclerosis & Plaque Dynamics — หน้า 5–6

> 📍 **ตำแหน่งในเอกสาร:** หน้า 5–6

### เนื้อหาจากสไลด์

#### หน้า 5: Pathogenesis
*   In more than 90% of cases, myocardial ischemia results from reduced blood flow due to obstructive **atherosclerotic lesions** in the epicardial coronary arteries.
*   It may be **chronic**, a narrowing of the coronary artery over time, and a limitation of the blood supply to part of the muscle.
*   Or it can be **acute**, resulting from a sudden rupture of a plaque and formation of a thrombus or blood clot.

#### หน้า 6: Atherosclerosis Progression & Plaque Types
*(สไลด์แสดงแผนภาพการดำเนินไปของโรค Atherosclerosis และภาพทางจุลพยาธิวิทยาของคราบไขมันชนิดต่างๆ)*

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 6)

> 🖼️ **คำอธิบายภาพ:**
> แผนภาพแสดงการพัฒนาของโรคหลอดเลือดแดงแข็ง (Atherosclerosis) แบ่งออกเป็น 2 ระยะหลัก:
> 1.  **Pre-Clinical Phase (มักพบในอายุน้อย):** เริ่มจากหลอดเลือดปกติ (Normal Artery) → เกิดคราบไขมันแรกเริ่ม (Fatty Streak) → พัฒนาเป็นคราบไขมันปนเส้นใย (Fibrofatty Plaque) → กลายเป็นคราบไขมันระยะลุกลามที่เปราะบาง (Advanced/Vulnerable Plaque) โดยมีปัจจัยกระตุ้นคือ Endothelial dysfunction, Monocyte adhesion, SMC proliferation และ Lipid accumulation
> 2.  **Clinical Phase (มักพบในวัยกลางคนถึงผู้สูงอายุ):** จาก Vulnerable Plaque สามารถดำเนินไปได้ 3 เส้นทางหลัก:
>     *   **Aneurysm and Rupture:** เกิดผนังหลอดเลือดโป่งพองและแตกออกจากการอ่อนแอของผนังหลอดเลือด
>     *   **Occlusion by Thrombus:** เกิดการแตก (Rupture), การกร่อน (Erosion), หรือการมีเลือดออกในคราบไขมัน (Plaque hemorrhage) นำไปสู่การกระตุ้นลิ่มเลือดอุดตันหลอดเลือดเฉียบพลัน
>     *   **Critical Stenosis:** คราบไขมันโตขึ้นเรื่อยๆ อย่างช้าๆ จนอุดตันรูหลอดเลือดอย่างรุนแรง
>
> ภาพตัดขวางทางจุลพยาธิวิทยาด้านล่างแสดงลักษณะของ Plaque 3 รูปแบบ:
> *   **Stable Plaque:** มี Fibrous cap หนาและแข็งแรง ล้อมรอบแกนไขมันขนาดเล็ก โอกาสแตกยาก
> *   **Unstable Plaque:** มี Fibrous cap บาง และมีแกนไขมันขนาดใหญ่ (Large lipid core) ร่วมกับมีเซลล์อักเสบสะสมอยู่มาก เสี่ยงต่อการฉีกขาดสูง
> *   **Disrupted Plaque:** เกิดการฉีกขาดของ Fibrous cap และมีลิ่มเลือด (Thrombus) ก่อตัวขึ้นด้านบนอุดตันรูหลอดเลือด

### 🧠 กลไกและเหตุผลทางการแพทย์
* **Vulnerable Plaque (คราบไขมันที่เปราะบาง)**: มีลักษณะสำคัญคือ Thin fibrous cap (ผนังเส้นใยบาง), Large necrotic lipid core (แกนไขมันขนาดใหญ่), และมีเซลล์อักเสบจำพวก Macrophages สะสมอยู่หนาแน่นที่บริเวณขอบ (Plaque shoulder) เซลล์อักเสบเหล่านี้จะหลั่งเอนไซม์ **Metalloproteinases (MMPs)** มาย่อยสลายคอลลาเจนใน Fibrous cap ทำให้ผนังบางลงเรื่อยๆ จนเกิดการฉีกขาด (Rupture) เมื่อสัมผัสกับแรงกระแทกของกระแสเลือด (Shear stress) นำไปสู่ภาวะหลอดเลือดอุดตันเฉียบพลัน (Acute Coronary Syndrome)

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* สาเหตุมากกว่า 90% ของโรคหัวใจขาดเลือดเกิดจาก **Atherosclerosis** ในหลอดเลือดหัวใจส่วนนอก (Epicardial coronary arteries)
* **Stable Plaque** นำไปสู่ภาวะขาดเลือดเรื้อรัง (Chronic Stable Angina) เนื่องจากรูหลอดเลือดค่อยๆ ตีบแคบลง
* **Unstable Plaque** (ผนังบาง ไขมันเยอะ อักเสบสูง) เสี่ยงต่อการแตกออก (Rupture) ซึ่งจะกระตุ้นการสร้างลิ่มเลือดอุดตันเฉียบพลัน นำไปสู่ภาวะกล้ามเนื้อหัวใจตายเฉียบพลัน (Acute MI)

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
✅ ข้อมูลสอดคล้องกับแหล่งอ้างอิงมาตรฐาน (*Robbins Basic Pathology*)

---

## Section 3: Consequences of Myocardial Ischemia & Angina Pectoris — หน้า 7–13

> 📍 **ตำแหน่งในเอกสาร:** หน้า 7–13

### เนื้อหาจากสไลด์

#### หน้า 7: Consequences of Myocardial Ischemia
*   **Myocardial infarction (MI)**, where ischemia causes frank cardiac necrosis.
*   **Angina pectoris ("chest pain")**, where ischemia is not severe enough to cause infarction, but the symptoms nevertheless portend infarction risk.
*   **Chronic IHD with heart failure**
*   **Sudden cardiac death (SCD)**

#### หน้า 8: Ischemic Cardiac Pain
*   **A. Common:** The pain most often radiates to the ulnar side of the left arm.
*   **B. Uncommon:** Less often the pain radiates to the right side, the neck, and the face, or to the dorsal side of the chest.

#### หน้า 9: Angina Pectoris
*   At least **70% occlusion** of coronary artery resulting in pain.
*   Usually brought on by physical exertion as the heart is trying to pump blood to the muscles, it requires more blood that is not available due to the blockage of the coronary artery/arteries.
*   Is self-limiting → usually stops when exertion is ceased.

#### หน้า 10: Angina Pectoris Classification
*   **Stable (typical)**
*   **Unstable (crescendo)**
*   **Prinzmetal's (variant)**

#### หน้า 11: Stable (typical) angina
*   Recurrent attacks of substernal or precordial chest discomfort caused by transient (**15s - 15 mins**) myocardial ischemia.
*   Imbalance in coronary perfusion relative to myocardial demand (physical activity, emotional excitement, psychological stress).
*   Usually relieved by rest or administering vasodilators (e.g., Nitroglycerin).
*   Myocardial ischemia that is insufficient to induce myocyte necrosis.

#### หน้า 12: Unstable angina
*   Increasingly frequent, prolonged (**>20 mins**), or severe angina or chest discomfort progressing at lower levels of physical activity or even occurring at rest.
*   Caused by the disruption of an atherosclerotic plaque.
*   **50% of patients** have evidence of myocardial infarction.

#### หน้า 13: Prinzmetal's (variant)
*   Rare, representing about two out of 100 cases of angina, and usually occurs in younger patients.
*   **Causes:** a spasm in the coronary arteries.
*   The coronary arteries can spasm as a result of: exposure to cold weather, stress, medicines, smoking, cocaine use.
*   **Symptoms:** pain or discomfort: usually occurs while resting and during the night or early morning hours.
*   Prinzmetal angina generally responds promptly to vasodilators, such as nitroglycerin and calcium channel blockers.

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 8)

> 🖼️ **คำอธิบายภาพ:**
> ภาพแสดงตำแหน่งการกระจายของอาการปวดเค้นอกจากการขาดเลือด (Referred Pain):
> *   **ภาพ A (พบบ่อย):** อาการปวดร้าวจากหน้าอกด้านซ้ายลงไปตามแนวแขนด้านในฝั่งนิ้วก้อย (Ulnar side of the left arm) และบริเวณหัวไหล่ซ้าย
> *   **ภาพ B (พบได้น้อยกว่า):** อาการปวดร้าวขึ้นไปที่ลำคอ, ขากรรไกร, ใบหน้า, ร้าวไปแขนขวา หรือร้าวทะลุไปที่บริเวณหลัง (Dorsal side of the chest)

### 🧠 กลไกและเหตุผลทางการแพทย์
1. **กลไกการเกิด Referred Pain**: เกิดจากเส้นประสาทรับความรู้สึกจากหัวใจ (Visceral afferent fibers) วิ่งเข้าสู่ไขสันหลังระดับเดียวกับเส้นประสาทรับความรู้สึกทางผิวหนังจากบริเวณหน้าอกและแขนซ้าย (Dermatomes T1-T5) ทำให้สมองแปลผลสัญญาณความเจ็บปวดสับสนและรู้สึกปวดที่บริเวณผิวหนังหน้าอกและแขนซ้ายแทนหัวใจ
2. **Critical Stenosis (70% Cutoff)**: ในสภาวะพักผ่อน (Rest) เลือดที่ไหลผ่านหลอดเลือดหัวใจที่ตีบต่ำกว่า 70% ยังเพียงพอต่อความต้องการ แต่เมื่อหลอดเลือดตีบ ≥ 70% (เรียกว่า Critical stenosis) หลอดเลือดจะไม่สามารถขยายตัวเพื่อเพิ่มการไหลเวียนเลือดเมื่อร่างกายออกกำลังกายได้ จึงเกิดอาการปวดเค้นอก (Angina)
3. **กลไกของ Prinzmetal's Angina**: เกิดจากภาวะหลอดเลือดหัวใจหดเกร็งตัวอย่างรุนแรง (Coronary artery vasospasm) โดยไม่สัมพันธ์กับการออกกำลังกาย มักเกิดในช่วงเช้ามืดขณะพักผ่อนเนื่องจากโทนประสาทพาราซิมพาเทติกสูงขึ้น หรือได้รับสารกระตุ้น เช่น โคเคน หรือการสูบบุหรี่ ซึ่งทำให้เกิด Endothelial dysfunction และการตอบสนองที่ไวเกินของกล้ามเนื้อเรียบหลอดเลือด

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* **Stable Angina** เกิดจากการตีบของหลอดเลือดคงที่ (≥ 70%) อาการปวดสัมพันธ์กับการออกกำลังกายหรือความเครียด หายได้เมื่อพักหรืออมยาใต้ลิ้น (Nitroglycerin) ภายใน 15 นาที และไม่มีการตายของกล้ามเนื้อหัวใจ
* **Unstable Angina** เกิดจากการฉีกขาดของคราบไขมัน มีอาการปวดรุนแรงขึ้น เจ็บขณะพัก หรือปวดนานกว่า 20 นาที ถือเป็นภาวะฉุกเฉินทางการแพทย์ที่เสี่ยงต่อการเกิดกล้ามเนื้อหัวใจตายเฉียบพลัน
* **Prinzmetal's Angina** เกิดจากหลอดเลือดหัวใจหดเกร็ง (Vasospasm) มักเกิดในคนอายุน้อยขณะพักหรือตอนกลางคืน รักษาโดยใช้ยาขยายหลอดเลือดกลุ่ม Nitrates และ Calcium Channel Blockers (CCBs)

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
* ‼️ **ในสไลด์ (หน้า 12):** "50% of patients [with unstable angina] have evidence of myocardial infarction."
* **ตามแหล่งอ้างอิง:** ตามเกณฑ์การวินิจฉัยปัจจุบันของ *AHA/ACC* และ *ESC Guidelines* หากผู้ป่วยมีหลักฐานการตายของกล้ามเนื้อหัวใจ (เช่น ระดับ Troponin สูงขึ้น) จะถูกจัดกลุ่มเป็น **NSTEMI** ทันที ส่วน **Unstable Angina** จะต้องมีผลตรวจ Cardiac Biomarkers เป็นลบ (ไม่มีกล้ามเนื้อหัวใจตาย) ดังนั้นประโยคนี้อาจหมายถึงผู้ป่วยที่มาด้วยอาการของ Unstable angina ในตอนแรก สุดท้ายแล้วประมาณครึ่งหนึ่งจะได้รับการวินิจฉัยว่าเป็น Myocardial Infarction (NSTEMI) หลังตรวจเลือด
* **แหล่งอ้างอิง:** *2021 AHA/ACC/ASE/CHEST/SAEM/SCCT/SCMR Guideline for the Evaluation and Diagnosis of Chest Pain* — https://www.ahajournals.org/doi/10.1161/CIR.0000000000001029

---

## Section 4: Myocardial Infarction (MI) Overview & Pathogenesis — หน้า 14–22

> 📍 **ตำแหน่งในเอกสาร:** หน้า 14–22

### เนื้อหาจากสไลด์

#### หน้า 14: Myocardial Infarction (MI)
*   MI, also known as **"heart attack,"** is the death of cardiac muscle resulting from ischemia.
*   Partial or total occlusion of one or more of the coronary arteries due to an atheroma, thrombus or emboli resulting in cell death (infarction) of the heart muscle.
*   250,000 deaths per year.
*   **30% mortality** within the first 2 hours.
*   **45 Minutes of Ischemia:** Cardiac muscle death occurs.

#### หน้า 15: Pathogenesis of Acute MI
*   Acute MI results from a dynamic interaction among several or all the following:
    *   Coronary atherosclerosis
    *   Acute atheromatous plaque change (such as rupture)
    *   Superimposed platelet activation
    *   Thrombosis
    *   Vasospasm
*   → resulting in an **occlusive intracoronary thrombus** overlying a disrupted plaque.

#### หน้า 16: Sequence of Events in Typical MI (Part 1)
*   The following sequence of events can be proposed:
    *   The initial event is a sudden change in the morphology of an atheromatous plaque, that is, **disruption**—manifest as intraplaque hemorrhage, erosion or ulceration, or rupture or fissuring.
    *   Exposed to subendothelial collagen and necrotic plaque contents, platelets undergo **adhesion, aggregation, activation**, and release of potent aggregators including thromboxane A2, serotonin, and platelet factors 3 and 4.

#### หน้า 17: Sequence of Events in Typical MI (Part 2)
*   **Vasospasm** is stimulated by platelet aggregation and the release of mediators.
*   Other mediators activate the **extrinsic pathway of coagulation**, adding to the bulk of the thrombus.
*   Frequently within minutes, the thrombus evolves to **completely occlude** the lumen of the coronary vessel.

#### หน้า 18: Myocardial Infarction Type 1 vs Type 2
*(สไลด์แสดงภาพเปรียบเทียบกลไกการเกิด MI Type 1 และ Type 2)*

#### หน้า 19: Atherosclerosis Progression Diagram (Robbins)
*(สไลด์แสดงแผนภาพการดำเนินโรคของ Atherosclerosis จากตำรา Robbins Basic Pathology)*

#### หน้า 20: Coronary Artery Pathology in Ischemic Heart Disease
| Syndrome | Stenosis | Plaque Disruption | Plaque-Associated Thrombus |
| :--- | :--- | :--- | :--- |
| **Stable angina** | >75% | No | No |
| **Unstable angina** | Variable | Frequent | Non-occlusive, often with thrombo-emboli |
| **Transmural MI** | Variable | Frequent | Occlusive |
| **Subendocardial MI** | Variable | Variable | Widely variable, may be absent, partial/complete, or lysed |
| **Sudden death** | Usually severe | Frequent | Often small platelet aggregates or thrombi and/or thrombo-emboli |

#### หน้า 21: Other Mechanisms Involved in MI
*   **Vasospasm:** with or without coronary atherosclerosis, perhaps in association with platelet aggregation (sometimes related to cocaine abuse).
*   **Emboli:** association with atrial fibrillation, a left-sided mural thrombus or vegetative endocarditis; or paradoxical emboli from the right side of the heart or the peripheral veins which cross to the systemic circulation, through a patent foramen ovale, causing coronary occlusion.
*   **Unexplained:** cases without detectable coronary atherosclerosis and thrombosis may be caused by diseases of small intramural coronary vessels, such as:
    *   Vasculitis
    *   Hematologic abnormalities such as hemoglobinopathies
    *   Amyloid deposition in vascular walls
    *   Other unusual disorders, such as vascular dissection.

#### หน้า 22: Atherosclerosis, Clot, and Spasm Diagrams
*(สไลด์แสดงภาพวาดเปรียบเทียบพยาธิสภาพ 3 รูปแบบ: Atherosclerosis with blood clot, Atherosclerosis เดี่ยวๆ, และ Spasm)*

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 18, 19, 22)

> 🖼️ **คำอธิบายภาพ หน้า 18:**
> ภาพเปรียบเทียบประเภทของกล้ามเนื้อหัวใจตายตามเกณฑ์สากล (Universal Definition of MI):
> *   **Myocardial Infarction Type 1:** เกิดจากพยาธิสภาพของคราบไขมันโดยตรง (Plaque rupture/erosion) ร่วมกับการเกิดลิ่มเลือดอุดตัน ทั้งแบบอุดตันสมบูรณ์ (Occlusive thrombus) หรืออุดตันบางส่วน (Non-occlusive thrombus)
> *   **Myocardial Infarction Type 2:** เกิดจากความไม่สมดุลระหว่าง Supply และ Demand ของออกซิเจน โดยไม่มีการแตกของ Plaque เฉียบพลัน สาเหตุรวมถึง: Atherosclerosis ร่วมกับภาวะขาดออกซิเจน, Coronary vasospasm, Microvascular dysfunction, Non-atherosclerotic coronary dissection (หลอดเลือดเซาะกร่อนเอง), หรือภาวะช็อก/ซีดรุนแรง (Oxygen supply/demand imbalance alone)

> 🖼️ **คำอธิบายภาพ หน้า 22:**
> ภาพวาดแสดงลักษณะทางกายวิภาคของหลอดเลือดหัวใจใน 3 ภาวะ:
> 1.  **Atherosclerosis with blood clot:** มีคราบไขมันหนาตัวที่ผนังหลอดเลือดและมีลิ่มเลือดสีแดงเข้มเกาะทับอุดตันรูหลอดเลือดเกือบทั้งหมด
> 2.  **Atherosclerosis:** มีเพียงคราบไขมันสีเหลืองสะสมหนาตัวทำให้รูหลอดเลือดตีบแคบลง แต่ไม่มีลิ่มเลือดอุดตัน
> 3.  **Spasm:** ผนังหลอดเลือดปกติไม่มีคราบไขมัน แต่มีการบีบเกร็งตัวของกล้ามเนื้อเรียบหลอดเลือดจนรูหลอดเลือดตีบแคบลงชั่วคราว

### 🧠 กลไกและเหตุผลทางการแพทย์
1. **กลไกการกระตุ้นเกล็ดเลือด (Platelet Activation Cascade)**: เมื่อ Plaque แตกออก คอลลาเจนใต้เยื่อบุหลอดเลือด (Subendothelial collagen) และ Von Willebrand Factor (vWF) จะสัมผัสกับเลือด กระตุ้นให้เกล็ดเลือดเข้ามาเกาะ (Adhesion) ผ่านตัวรับ `GP Ib/IX/V` จากนั้นเกล็ดเลือดจะหลั่งสารกระตุ้น ได้แก่ **ADP** และ **Thromboxane A2 (TxA2)** ซึ่งทำหน้าที่เรียกเกล็ดเลือดตัวอื่นมารวมกลุ่มกัน (Aggregation) ผ่านตัวรับ `GP IIb/IIIa` เกิดเป็นลิ่มเลือดเกล็ดเลือดแรกเริ่ม (White thrombus)
2. **การกระตุ้น Coagulation Cascade**: เนื้อเยื่อที่ฉีกขาดจะหลั่ง **Tissue Factor (Factor III)** ออกมากระตุ้น Extrinsic pathway นำไปสู่การสร้าง **Fibrin** มาสานถักทอครอบลิ่มเลือดเกล็ดเลือด ทำให้กลายเป็นลิ่มเลือดที่แข็งแรงและอุดตันหลอดเลือดอย่างสมบูรณ์ (Red thrombus)
3. **ความสำคัญของเวลา 45 นาที**: เซลล์กล้ามเนื้อหัวใจที่ขาดเลือดอย่างรุนแรงจะเริ่มเกิดการบาดเจ็บแบบย้อนกลับไม่ได้ (Irreversible injury) และเริ่มตาย (Necrosis) หลังจากผ่านไป 20-40 นาที ดังนั้นการเปิดหลอดเลือดอย่างรวดเร็ว (Reperfusion) ภายในระยะเวลานี้จึงมีความสำคัญสูงสุดในการรักษาชีวิตเนื้อเยื่อหัวใจ

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* **Type 1 MI** เกิดจากคราบไขมันแตก (Plaque rupture) แล้วมีลิ่มเลือดอุดตันเฉียบพลัน (เป็นสาเหตุที่พบบ่อยที่สุด)
* **Type 2 MI** เกิดจากความไม่สมดุลของ Supply/Demand โดยไม่มี Plaque แตก เช่น จากภาวะความดันโลหิตต่ำรุนแรง, โลหิตจาง, หรือหลอดเลือดหดเกร็ง
* กลไกการเกิดลิ่มเลือดอุดตันเริ่มจาก **Plaque rupture** → **Platelet adhesion & aggregation** → **Coagulation cascade activation** → **Occlusive thrombus**

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
* ‼️ **ในสไลด์ (หน้า 14):** "250,000 deaths per year [from MI]."
* **ตามแหล่งอ้างอิง:** ตัวเลขนี้เป็นสถิติเก่าเฉพาะในสหรัฐอเมริกา ปัจจุบันตามรายงานของ *AHA Heart Disease and Stroke Statistics 2023* มีผู้เสียชีวิตจากโรคหลอดเลือดหัวใจ (Coronary Heart Disease) ในสหรัฐฯ ประมาณ 380,000 รายต่อปี และในระดับโลกมีผู้เสียชีวิตสูงถึง 9 ล้านรายต่อปี
* **แหล่งอ้างอิง:** *AHA Heart Disease and Stroke Statistics 2023 Update* — https://www.ahajournals.org/doi/10.1161/CIR.0000000000001123

---

## Section 5: Coronary Anatomy, Myocyte Injury Timeline & Patterns of Infarction — หน้า 23–27

> 📍 **ตำแหน่งในเอกสาร:** หน้า 23–27

### เนื้อหาจากสไลด์

#### หน้า 23: Frequencies of Critical Narrowing in Coronary Arteries
*   The frequencies of critical narrowing (and thrombosis) of each of the three main arterial trunks and the corresponding sites of myocardial lesions resulting in infarction (in the typical right dominant heart) are as follows:
    *   **40-50%:** **Anterior Descending Branch of Left Coronary Artery (LAD)**
        *   Anterior wall of left ventricle
        *   Front 2/3 of septum, including the bundle branches
    *   **30-40%:** **Right Coronary Artery (RCA)**
        *   Inferior wall of left ventricle (in most people)
        *   Right ventricle
        *   Right atrium, including SA and AV nodes (most people)
    *   **15-20%:** **Circumflex Branch of Left Coronary Artery (LCX)**
        *   High lateral wall of LV
        *   Some of posterior wall (varies in people)

#### หน้า 24-25: Key Events in Ischemic Cardiac Myocytes
*   **Table 12-4: Approximate Time of Onset of Key Events in Ischemic Cardiac Myocytes**
| Feature | Time |
| :--- | :--- |
| **Onset of ATP depletion** | Seconds |
| **Loss of contractility** | <2 minutes |
| **ATP reduced to 50% of normal** | 10 minutes |
| **ATP reduced to 10% of normal** | 40 minutes |
| **Irreversible cell injury** | 20-40 minutes |
| **Microvascular injury** | >1 hour |

#### หน้า 26: Pattern of Infarction
*   **Transmural Infarction:** Ischemic necrosis involves the full or nearly full thickness of the ventricular wall.
*   **Subendocardial (non-transmural) Infarction:** Ischemic necrosis limited to the inner one-third or at most one-half of the ventricular wall.
*   **Multifocal microinfarction:** Involving only smaller intramural vessels, such as microembolization, vasculitis, or vascular spasm.

#### หน้า 27: Distribution of Myocardial Ischemic Necrosis
*(สไลด์แสดงแผนภาพเปรียบเทียบพยาธิสภาพการตายของกล้ามเนื้อหัวใจแบบ Transmural และ Non-transmural)*

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 23, 24, 27)

> 🖼️ **คำอธิบายภาพ หน้า 23:**
> ภาพวาดแสดงกายวิภาคของหลอดเลือดหัวใจหลัก 3 เส้น และอัตราส่วนการเกิดอุดตันที่พบบ่อย:
> 1.  **LAD (40-50%):** ทอดผ่านด้านหน้าของหัวใจ เลี้ยงผนังหน้าหัวใจห้องล่างซ้ายและผนังกั้นห้องหัวใจส่วนหน้า
> 2.  **RCA (30-40%):** อ้อมไปทางขวาและอ้อมไปเลี้ยงด้านล่าง/หลังของหัวใจ รวมถึงระบบนำไฟฟ้า (SA/AV node)
> 3.  **LCX (15-20%):** อ้อมไปทางซ้าย เลี้ยงผนังด้านข้างของหัวใจห้องล่างซ้าย

> 🖼️ **คำอธิบายภาพ หน้า 24:**
> แผนภาพแสดงการดำเนินไปของการตายของเนื้อเยื่อหัวใจ (Wavefront of Necrosis):
> *   เมื่อหลอดเลือดอุดตันเฉียบพลัน การตายของเซลษ์จะเริ่มจากบริเวณ **Subendocardium** (เนื้อเยื่อชั้นในสุดใต้เยื่อบุหัวใจ) เสมอ เนื่องจากเป็นจุดที่อยู่ไกลจากหลอดเลือดหัวใจส่วนนอก (Epicardial vessels) มากที่สุด และได้รับแรงกดทับจากความดันในห้องหัวใจสูงที่สุด
> *   หากปล่อยทิ้งไว้โดยไม่เปิดหลอดเลือด (Reperfusion) ภายใน 2-24 ชั่วโมง การตายจะขยายขอบเขตออกไปสู่ชั้นนอกเรื่อยๆ จนกลายเป็นการตายตลอดความหนาของผนังหัวใจ (**Transmural Infarction**)

> 🖼️ **คำอธิบายภาพ หน้า 27:**
> แผนภาพเปรียบเทียบรูปแบบการตายของกล้ามเนื้อหัวใจห้องล่างซ้าย (LV):
> *   **Transmural Infarcts (คอลัมน์ซ้าย):** เกิดจากการอุดตันอย่างถาวรของหลอดเลือดหลัก (LAD, LCX, หรือ RCA) ส่งผลให้เนื้อตายกินพื้นที่เต็มความหนาของผนังหัวใจเฉพาะส่วน (Regional)
> *   **Non-Transmural Infarcts (คอลัมน์ขวา):**
>     *   *Transient/Partial obstruction:* เกิดเนื้อตายเฉพาะชั้น Subendocardium เฉพาะส่วน (Regional subendocardial infarct)
>     *   *Global hypotension:* เกิดภาวะความดันโลหิตต่ำทั่วร่างกาย ส่งผลให้เกิดเนื้อตายชั้น Subendocardium รอบวงหัวใจ (Circumferential subendocardial infarct)
>     *   *Small vessel occlusions:* เกิดเนื้อตายขนาดเล็กกระจายตัวทั่วไป (Microinfarcts) จากการอุดตันของหลอดเลือดฝอย

### 🧠 กลไกและเหตุผลทางการแพทย์
1. **ทำไมกล้ามเนื้อหัวใจหยุดบีบตัวใน 2 นาที?**: เมื่อขาดออกซิเจน กระบวนการสร้างพลังงานแบบ Oxidative phosphorylation ในไมโทคอนเดรียจะหยุดลงทันที เซลล์ต้องเปลี่ยนไปใช้การสลายกลูโคสแบบไม่ใช้ออกซิเจน (Anaerobic glycolysis) ซึ่งสร้าง ATP ได้น้อยมากและทำให้เกิดกรดแล็คติกสะสม ความเป็นกรดที่สูงขึ้นร่วมกับการขาด ATP ส่งผลให้ Myofibrils ไม่สามารถทำงานบีบตัวได้ เพื่อถนอมพลังงานที่เหลืออยู่ไว้ใช้ในการรักษาสภาพเซลล์ (Cell viability)
2. **ทำไม Subendocardium จึงไวต่อการขาดเลือดที่สุด?**:
    * **Anatomical factor:** หลอดเลือดโคโรนารีวิ่งจากชั้นนอก (Epicardium) แขนงย่อยจึงต้องแทงทะลุผ่านกล้ามเนื้อหัวใจลงไปเลี้ยงชั้นในสุด (Subendocardium) ทำให้แรงดันเลือดที่ไปถึงชั้นในสุดต่ำที่สุดอยู่แล้ว
    * **Mechanical factor:** ขณะหัวใจบีบตัว (Systole) แรงดันในห้องหัวใจจะกดทับหลอดเลือดฝอยในชั้น Subendocardium อย่างรุนแรง ทำให้เลือดไหลเวียนได้เฉพาะช่วงหัวใจคลายตัว (Diastole) เท่านั้น

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* หลอดเลือดหัวใจที่เกิดการอุดตันบ่อยที่สุดคือ **LAD (40-50%)** เลี้ยงผนังหน้าหัวใจห้องล่างซ้าย (Anterior LV)
* หลังขาดเลือด กล้ามเนื้อหัวใจจะหยุดบีบตัวภายใน **2 นาที** และจะเริ่มเกิดการตายอย่างถาวร (Irreversible injury) ตั้งแต่นาทีที่ **20-40** เป็นต้นไป โดยเริ่มจากชั้น **Subendocardium** เสมอ
* **Transmural MI** คือการตายตลอดความหนาของผนังหัวใจ มักเกิดจากการอุดตันของหลอดเลือดหลักอย่างถาวร ส่วน **Subendocardial MI** จะตายเฉพาะชั้นใน มักเกิดจากหลอดเลือดอุดตันบางส่วนหรือมีความดันโลหิตต่ำรุนแรง

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
✅ ข้อมูลสอดคล้องกับพยาธิวิทยามาตรฐานทางการแพทย์

---

## Section 6: Pathology of MI: Morphologic Changes & Histology — หน้า 28–30

> 📍 **ตำแหน่งในเอกสาร:** หน้า 28–30

### เนื้อหาจากสไลด์

#### หน้า 28: Evolution of Morphologic Changes in Myocardial Infarction
*   **Table 12-5: Evolution of Morphologic Changes in Myocardial Infarction**
| Time | Gross Features | Light Microscope | Electron Microscope |
| :--- | :--- | :--- | :--- |
| **Reversible Injury** | | | |
| 0 - 1/2 hr | None | None | Relaxation of myofibrils; glycogen loss; mitochondrial swelling |
| **Irreversible Injury** | | | |
| 1/2 - 4 hr | None | Usually none; variable waviness of fibers at border | Sarcolemmal disruption; mitochondrial amorphous densities |
| 4 - 12 hr | Dark mottling (occasional) | Early coagulation necrosis; edema; hemorrhage | |
| 12 - 24 hr | Dark mottling | Ongoing coagulation necrosis; pyknosis of nuclei; myocyte hypereosinophilia; marginal contraction band necrosis; early neutrophilic infiltrate | |
| 1 - 3 days | Mottling with yellow-tan infarct center | Coagulation necrosis, with loss of nuclei and striations; brisk interstitial infiltrate of neutrophils | |
| 3 - 7 days | Hyperemic border; central yellow-tan softening | Beginning disintegration of dead myofibers, with dying neutrophils; early phagocytosis of dead cells by macrophages at infarct border | |
| 7 - 10 days | Maximally yellow-tan and soft, with depressed red-tan margins | Well-developed phagocytosis of dead cells; granulation tissue at margins | |
| 10 - 14 days | Red-gray depressed infarct borders | Well-established granulation tissue with new blood vessels and collagen deposition | |
| 2 - 8 wk | Gray-white scar, progressive from border toward core of infarct | Increased collagen deposition, with decreased cellularity | |
| >2 mo | Scarring complete | Dense collagenous scar | |

#### หน้า 29: Gross Pathology of Acute MI
*(สไลด์แสดงภาพตัดขวางของหัวใจที่ย้อมด้วยสารเคมีพิเศษเพื่อตรวจหาเนื้อตาย)*

#### หน้า 30: Microscopic Features of MI and Repair
*(สไลด์แสดงภาพจุลพยาธิวิทยาของกล้ามเนื้อหัวใจในระยะต่างๆ ตั้งแต่ 1 วัน จนถึงกลายเป็นแผลเป็น)*

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 29, 30)

> 🖼️ **คำอธิบายภาพ หน้า 29:**
> ภาพถ่ายมหพยาธิวิทยา (Gross pathology) ของหัวใจตัดขวาง ย้อมด้วยสาร **Triphenyltetrazolium chloride (TTC)**:
> *   บริเวณกล้ามเนื้อหัวใจปกติที่ยังมีชีวิตอยู่จะย้อมติดสีแดงเข้มเนื่องจากยังมีเอนไซม์ Lactate dehydrogenase (LDH) ทำปฏิกิริยากับสารย้อม
> *   บริเวณที่เกิดกล้ามเนื้อหัวใจตายเฉียบพลัน (Acute infarct) บริเวณผนังหลังและข้าง (Posterolateral LV) จะย้อมไม่ติดสี ทำให้เห็นเป็นสีซีดขาว/เหลือง (ลูกศรชี้) เนื่องจากเซลล์ที่ตายจะสูญเสีย LDH รั่วไหลออกนอกเซลล์
> *   ภาพยังแสดงรอยแผลเป็นสีขาวซีดขนาดเล็กที่ผนังหน้า (หัวลูกศรชี้) ซึ่งบ่งบอกถึงประวัติการเกิดกล้ามเนื้อหัวใจตายในอดีต (Old infarct)

> 🖼️ **คำอธิบายภาพ หน้า 30:**
> ภาพทางจุลพยาธิวิทยาแสดงระยะการซ่อมแซมของกล้ามเนื้อหัวใจหลังเกิด MI:
> *   **ภาพ A (1 วัน):** แสดงลักษณะ Coagulative necrosis เซลล์กล้ามเนื้อหัวใจติดสีชมพูเข้มขึ้น (Hypereosinophilia) นิวเคลียสเริ่มสลายตัว และเห็นเส้นใยบิดเบี้ยวเป็นลอนคลื่น (Wavy fibers)
> *   **ภาพ B (3-4 วัน):** มีเซลล์อักเสบชนิด Neutrophils (นิวเคลียสหลายพู) เข้ามาจับกลุ่มหนาแน่นในช่องว่างระหว่างเซลล์เพื่อย่อยสลายเนื้อตาย
> *   **ภาพ C (7-10 วัน):** เซลล์ Neutrophils เริ่มตาย และมี Macrophages เข้ามาทำหน้าที่กลืนกินเศษเซลล์ที่ตาย (Phagocytosis)
> *   **ภาพ D (10-14 วัน):** เริ่มสร้าง Granulation tissue ประกอบด้วยหลอดเลือดฝอยขนาดเล็กที่สร้างขึ้นใหม่ (Neovascularization) และเซลล์สร้างเส้นใย (Fibroblasts)
> *   **ภาพ E (มากกว่า 2 เดือน):** เนื้อตายถูกแทนที่โดยสมบูรณ์ด้วยแผลเป็นคอลลาเจนหนาแน่น (Dense collagenous scar) ย้อมติดสีฟ้าเข้มด้วยสีย้อมพิเศษ (Trichrome stain)

### 🧠 กลไกและเหตุผลทางการแพทย์
1. **ทำไมช่วงวันที่ 3-7 จึงเสี่ยงต่อการเกิดหัวใจทะลุสูงสุด?**: ในช่วงเวลานี้ Macrophages จะหลั่งเอนไซม์ออกมาย่อยสลายโครงสร้างคอลลาเจนเดิมของกล้ามเนื้อหัวใจที่ตายเพื่อเตรียมพื้นที่สำหรับการสร้างแผลเป็นใหม่ ทำให้ผนังหัวใจบริเวณนั้นมีความอ่อนนุ่มและเปราะบางที่สุด (Myomalacia cordis) ขณะที่เนื้อเยื่อเกี่ยวพันใหม่ (Granulation tissue) ยังสร้างขึ้นมาไม่แข็งแรงพอ หากผู้ป่วยมีความดันโลหิตสูงในช่วงนี้ จะเสี่ยงต่อการเกิดผนังหัวใจทะลุ (Myocardial rupture) สูงมาก
2. **หลักการย้อม TTC**: TTC เป็นสารรับอิเล็กตรอน เมื่อสัมผัสกับเซลล์ที่มีชีวิต เอนไซม์ Dehydrogenase (โดยเฉพาะ LDH) จะรีดิวซ์ TTC ให้กลายเป็นสารสีแดงที่ไม่ละลายน้ำ (Formazan) แต่ในเซลล์ที่ตาย เยื่อหุ้มเซลล์จะฉีกขาดทำให้ LDH รั่วไหลออกไปหมด จึงย้อมไม่ติดสีและเห็นเป็นสีซีด

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* **ช่วง 0-12 ชั่วโมงแรก**: แทบไม่เห็นการเปลี่ยนแปลงทางมหพยาธิวิทยา (Gross) ด้วยตาเปล่า
* **ช่วง 1-3 วัน**: จะเห็นเนื้อตายสีเหลือง-เทาชัดเจน และมีเซลล์ **Neutrophils** เข้ามามากที่สุด
* **ช่วง 3-7 วัน**: เป็นช่วงที่เนื้อหัวใจอ่อนนุ่มที่สุด เสี่ยงต่อภาวะแทรกซ้อนรุนแรง เช่น **ผนังหัวใจทะลุ (Rupture)**
* **การซ่อมแซมแผลเป็น**: จะเสร็จสมบูรณ์กลายเป็นแผลเป็นสีขาวแข็ง (Dense collagenous scar) หลังจากเกิดเหตุการณ์ประมาณ **2 เดือน** ขึ้นไป

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
✅ ข้อมูลสอดคล้องกับพยาธิวิทยามาตรฐานทางการแพทย์ (*Robbins Pathologic Basis of Disease*)

---

## Section 7: Pathophysiology, Biomarkers & Diagnosis of ACS — หน้า 31–33

> 📍 **ตำแหน่งในเอกสาร:** หน้า 31–33

### เนื้อหาจากสไลด์

#### หน้า 31: Biochemical Changes & Salvageable Myocardium Graphs
*(สไลด์แสดงกราฟความสัมพันธ์ระหว่างสารเคมีในเซลล์กับเวลา และสัดส่วนเนื้อหัวใจที่ช่วยชีวิตได้)*

#### หน้า 32: Biomarkers of Myocardial Infarction (Troponin)
*   **1. Onset of myocardial infarction**
*   **2. Plasma membrane of necrotic myocytes becomes leaky**
*   **3. Troponin leaks out of cell into circulation**
*   **4. Biomarker for diagnosis of myocardial infarction**
*   **Troponin Concentration Ranges:**
    *   `0.001 µg/L` → Healthy
    *   `0.01 µg/L` → Stable Angina, Chronic heart failure
    *   `0.1 µg/L` → Micro MI, Myocarditis, Acute heart failure
    *   `1 µg/L` → Small MI, Myocarditis, Pulmonary embolism
    *   `10 µg/L` → Medium sized MI, Severe myocarditis
    *   `100 µg/L` → Large MI
*   **Symptoms:** Chest Pain, Increase in level of cardiac biomarkers
*   **MI detection:** ECG, Cardiac biomarker detection

#### หน้า 33: Acute Coronary Syndrome (ACS) Diagnostic Flowchart
*(สไลด์แสดงแผนผังการวินิจฉัยแยกโรคในกลุ่มอาการโคโรนารีเฉียบพลัน)*

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 31, 32, 33)

> 🖼️ **คำอธิบายภาพ หน้า 31:**
> *   **กราฟ A:** แสดงระดับ ATP และ Lactate ในเซลล์หลังเกิดการขาดเลือด แกนนอนคือเวลา (นาที) แกนตั้งคือความเข้มข้น พบว่าระดับ ATP (เส้นสีแดง) ลดลงอย่างรวดเร็วเกือบเหลือศูนย์ภายใน 40 นาที ขณะที่ระดับ Lactate (เส้นสีเหลือง) สูงขึ้นอย่างต่อเนื่องจากการสลายพลังงานแบบไม่ใช้ออกซิเจน
> *   **กราฟ B:** แสดงสัดส่วนของกล้ามเนื้อหัวใจที่เสี่ยงต่อการตาย (Fraction of at-risk myocardium) แกนนอนคือเวลา (ชั่วโมง) พบว่าในช่วง 0 ถึง 30 นาทีแรกเป็นระยะที่ย้อนกลับได้ (Reversible phase) หากเปิดหลอดเลือดได้ทันจะสามารถช่วยชีวิตกล้ามเนื้อหัวใจได้เกือบ 100% แต่หลังจาก 40 นาทีขึ้นไปจะเข้าสู่ระยะที่ย้อนกลับไม่ได้ (Irreversible phase) สัดส่วนของเนื้อตายสะสม (Cumulative dead myocardium) จะเพิ่มขึ้นเรื่อยๆ จนกระทั่งหลัง 6-12 ชั่วโมง กล้ามเนื้อหัวใจที่เสี่ยงทั้งหมดจะตายโดยสมบูรณ์

> 🖼️ **คำอธิบายภาพ หน้า 32:**
> *   ภาพวาดแสดงกลไกการหลั่ง Troponin: เมื่อเกิดกล้ามเนื้อหัวใจตาย เยื่อหุ้มเซลล์จะฉีกขาด ทำให้ Troponin complex ที่เกาะอยู่บนเส้นใย Actin หลุดลอยเป็นอิสระและรั่วไหลเข้าสู่กระแสเลือดผ่านทางหลอดเลือดฝอย
> *   กราฟแสดงระดับความเข้มข้นของ Cardiac Troponin ในกระแสเลือดตามจำนวนวันหลังเกิด MI: ระดับ Troponin จะเริ่มสูงขึ้นภายใน 3-4 ชั่วโมงหลังเกิดอาการ และจะขึ้นสูงสุด (Peak) ในวันที่ 1-2 จากนั้นจะค่อยๆ ลดลงแต่ยังคงตรวจพบได้นานถึง 7-10 วัน (เส้นประสีม่วงแสดงกรณีที่ได้รับการเปิดหลอดเลือดสำเร็จ ระดับ Troponin จะขึ้นสูงอย่างรวดเร็วและลดลงเร็วกว่าเนื่องจากเกิดปรากฏการณ์ Washout)

> 🖼️ **คำอธิบายภาพ หน้า 33:**
> แผนผังการวินิจฉัยแยกโรคผู้ป่วยที่มาด้วยอาการเจ็บหน้าอกเฉียบพลัน (Acute Coronary Syndrome - ACS):
> 1.  **Admission:** ผู้ป่วยมาโรงพยาบาลด้วยอาการเจ็บหน้าอกเฉียบพลัน
> 2.  **ECG:** ตรวจคลื่นไฟฟ้าหัวใจทันที แบ่งเป็น 3 รูปแบบหลัก:
>     *   *Persistent ST-elevation:* มีการยกขึ้นของช่วง ST อย่างต่อเนื่อง → วินิจฉัยเป็น **STEMI** (ST-Elevation Myocardial Infarction) ทันทีโดยไม่ต้องรอผลเลือด
>     *   *ST/T abnormalities:* มีคลื่นไฟฟ้าหัวใจผิดปกติแต่ไม่มี ST ยก (เช่น ST depression หรือ T-wave inversion)
>     *   *Normal or undetermined ECG:* คลื่นไฟฟ้าหัวใจปกติหรือก้ำกึ่ง
> 3.  **Bio-chemistry:** ตรวจระดับเอนไซม์กล้ามเนื้อหัวใจ (Troponin):
>     *   หากระดับ Troponin สูงขึ้นหรือมีการเปลี่ยนแปลงขึ้น-ลง (Rise/Fall) → วินิจฉัยเป็น **NSTEMI** (Non-ST-Elevation Myocardial Infarction)
>     *   หากระดับ Troponin ปกติ → วินิจฉัยเป็น **Unstable Angina**

### 🧠 กลไกและเหตุผลทางการแพทย์
1. **ทำไม Troponin จึงเป็น Gold Standard?**: เดิมทีมีการใช้เอนไซม์ CK-MB ในการวินิจฉัย แต่ CK-MB สามารถพบได้ในกล้ามเนื้อลายเช่นกันเมื่อเกิดการบาดเจ็บ ส่วน **Cardiac Troponin (cTnI และ cTnT)** มีโครงสร้างกรดอะมิโนเฉพาะตัวที่พบในกล้ามเนื้อหัวใจเท่านั้น (Cardiospecificity สูงมาก) ทำให้มีความไวและความจำเพาะในการวินิจฉัยกล้ามเนื้อหัวใจตายสูงที่สุดในปัจจุบัน
2. **ความสำคัญของระดับ Troponin**: ระดับ Troponin ในเลือดมีความสัมพันธ์โดยตรงกับขนาดของเนื้อตาย (Infarct size) ยิ่งค่าสูงมาก (เช่น > 100 μg/L) บ่งบอกถึงการตายของกล้ามเนื้อหัวใจเป็นบริเวณกว้าง ซึ่งพยากรณ์โรคไม่ดีและเสี่ยงต่อการเกิดภาวะหัวใจล้มเหลวตามมา

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* **STEMI** วินิจฉัยจากอาการเจ็บหน้าอกร่วมกับคลื่นไฟฟ้าหัวใจพบ **ST-elevation** ต้องรีบส่งเปิดหลอดเลือดทันทีโดยไม่ต้องรอผลเลือด
* **NSTEMI** และ **Unstable Angina** มีอาการคล้ายกันและไม่มี ST-elevation ใน ECG แต่แยกกันที่ผลเลือด: **NSTEMI จะมีระดับ Troponin สูงขึ้น** ส่วน **Unstable Angina ระดับ Troponin จะปกติ**
* **Troponin** เป็นสารบ่งชี้ทางชีวภาพที่มีความจำเพาะต่อกล้ามเนื้อหัวใจสูงที่สุด เริ่มสูงขึ้นในเลือดหลังเกิดอาการ 3-4 ชั่วโมง และอยู่ได้นานถึง 7-10 วัน

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
✅ ข้อมูลสอดคล้องกับแนวทางเวชปฏิบัติสากล (*AHA/ACC และ ESC Guidelines*)

---

## Section 8: Pre-hospital Assessment, Thai ACS Guidelines & Reperfusion — หน้า 34–35

> 📍 **ตำแหน่งในเอกสาร:** หน้า 34–35

### เนื้อหาจากสไลด์

#### หน้า 34: Pre-hospital Assessment and Management (AHA Guideline)
*   **Pre-hospital Assessment and Management Considerations for Suspected ACS**
*   **Suspected ACS** → Evaluation by Emergency Medical Services → **12-Lead ECG** (Within 10 minutes of First Medical Contact).
*   **STEMI:** Immediate transfer to PCI-capable hospital. Goal of First Medical Contact to Device Time **≤ 90 minutes**.
*   **Non-Diagnostic For STEMI:** Transport to Local Emergency Department. Further in-hospital assessment of confirmed or suspected ACS.
*   **Serial ECGs:** To detect potential ischemic changes, especially if clinical suspicion for ACS remains high.
*   **In patients with STEMI managed with primary PCI:**
    *   Each **30 minute delay** is associated with a **7.5% relative risk** of 1-year death.

#### หน้า 35: Thai Acute Coronary Syndromes Guidelines 2020
*   **แนวทางปฏิบัติการดูแลรักษาผู้ป่วยภาวะหัวใจขาดเลือดเฉียบพลัน พ.ศ. 2563**
*   **First medical contact (FMC)** หมายถึงผู้เห็นเหตุการณ์คนแรก ณ จุดแรกที่พบผู้ป่วย
*   **STEMI diagnosis** ต้องทำภายใน **<10 นาที**
*   **Reperfusion Strategy Decision:**
    *   หากส่งตัวไปถึงโรงพยาบาลที่ทำ PCI ได้ภายใน **≤ 120 นาที** → เลือก **Primary PCI** (Reperfusion strategy: Wire Crossing)
    *   หากใช้เวลาส่งตัวมากกว่า **> 120 นาที** → เลือก **Fibrinolysis strategy** (Reperfusion strategy: Needle) ทันที

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 35)

> 🖼️ **คำอธิบายภาพ หน้า 35:**
> แผนผังการส่งต่อผู้ป่วย STEMI ตามแนวทางเวชปฏิบัติของประเทศไทยปี 2020 (Thai ACS Guidelines 2020):
> *   **กรณีที่ 1: FMC ณ โรงพยาบาลที่ไม่สามารถทำ PCI ได้ (เช่น รพ.ชุมชน):**
>     *   ต้องวินิจฉัย STEMI จาก ECG ให้ได้ภายใน 10 นาที
>     *   ประเมินระยะเวลาในการส่งตัวไปถึงห้องสวนหัวใจ (Cath lab) เพื่อทำ PCI:
>         *   หากใช้เวลา **≤ 120 นาที** → ส่งต่อเพื่อทำ **Primary PCI** (เป้าหมายเวลาตั้งแต่แรกพบจนถึงเปิดหลอดเลือดด้วยสายสวนต้องสั้นที่สุด)
>         *   หากใช้เวลา **> 120 นาที** → ให้ยาละลายลิ่มเลือด (**Fibrinolytic therapy**) ทางหลอดเลือดดำทันที ณ โรงพยาบาลแห่งนั้นเพื่อเปิดหลอดเลือดเบื้องต้นก่อนส่งต่อ
> *   **กรณีที่ 2: FMC ณ โรงพยาบาลที่สามารถทำ PCI ได้อยู่แล้ว:**
>     *   ต้องวินิจฉัย STEMI ให้ได้ภายใน 10 นาที และส่งผู้ป่วยเข้าห้องสวนหัวใจเพื่อทำ **Primary PCI** ทันที โดยมีเป้าหมายเวลาตั้งแต่แรกพบจนถึงเปิดหลอดเลือด (FMC-to-Device) **< 90 นาที**

### 🧠 กลไกและเหตุผลทางการแพทย์
1. **ทำไมความล่าช้าทุก 30 นาทีจึงเพิ่มอัตราการเสียชีวิต 7.5%?**: กล้ามเนื้อหัวใจที่ขาดเลือดจะตายเพิ่มขึ้นเรื่อยๆ ตามเวลาที่ผ่านไป (Time is muscle) การเปิดหลอดเลือดที่ล่าช้าส่งผลให้เกิดเนื้อตายเป็นบริเวณกว้างขึ้น นำไปสู่ภาวะหัวใจล้มเหลวรุนแรง, หัวใจเต้นผิดจังหวะชนิดรุนแรง (Lethal arrhythmia), หรือเกิดภาวะช็อกจากการทำงานของหัวใจล้มเหลว (Cardiogenic shock) ซึ่งเป็นสาเหตุหลักของการเสียชีวิต
2. **กลไกของยาละลายลิ่มเลือด (Fibrinolytic drugs)**: ยาในกลุ่มนี้ (เช่น Streptokinase, Alteplase, Tenecteplase) ทำหน้าที่กระตุ้นการเปลี่ยน Plasminogen ให้กลายเป็น **Plasmin** ซึ่งเป็นเอนไซม์ที่มีหน้าที่ย่อยสลายเส้นใย Fibrin ที่ยึดเกาะลิ่มเลือดอยู่ ทำให้ลิ่มเลือดสลายตัวและเปิดทางให้เลือดกลับไปเลี้ยงหัวใจได้อีกครั้ง

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* เมื่อผู้ป่วยสงสัยภาวะ ACS มาถึงจุดบริการทางการแพทย์แรก (FMC) จะต้องได้รับการตรวจคลื่นไฟฟ้าหัวใจ (12-lead ECG) และแปลผลให้เสร็จสิ้นภายใน **10 นาที**
* หากเป็น **STEMI** และอยู่ในโรงพยาบาลที่ทำ PCI ได้ ต้องเปิดหลอดเลือดให้ได้ภายใน **90 นาที**
* หากอยู่ในโรงพยาบาลที่ทำ PCIไม่ได้ และประเมินว่าส่งต่อใช้เวลา **เกิน 120 นาที** ให้พิจารณาให้ยาละลายลิ่มเลือด (Fibrinolysis) ทันที ห้ามรอส่งตัวโดยไม่ได้ให้ยา

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
✅ ข้อมูลสอดคล้องกับแนวทางเวชปฏิบัติของสมาคมแพทย์โรคหัวใจแห่งประเทศไทยปี 2563 (*Thai ACS Guidelines 2020*)

---

## Section 9: Complications of Myocardial Infarction — หน้า 36–38

> 📍 **ตำแหน่งในเอกสาร:** หน้า 36–38

### เนื้อหาจากสไลด์

#### หน้า 36: Complications of Myocardial Infarction Flowchart
*   **Myocardial Infarction Complications:**
    *   **Impaired contractility**
        *   → Ventricular thrombus → **Stroke (embolism)**
        *   → Hypotension → decrease coronary perfusion → increase ischemia → **Cardiogenic shock**
        *   → **Congestive heart failure**
    *   **Tissue necrosis**
        *   → Papillary muscle infarction → Mitral regurgitation → **Congestive heart failure**
        *   → Ventricular wall rupture → **Cardiac tamponade**
    *   **Electrical instability**
        *   → **Arrhythmias**
    *   **Pericardial inflammation**
        *   → **Pericarditis**

#### หน้า 37: Timeline of MI Complications
*   **Acute MI** → Timeline of complications:
    *   **< 4 hours:** Ventricular arrhythmias (ventricular fibrillation or tachycardia) - Primary: due to ischemia.
    *   **< 24 hours:** Bradyarrhythmias / heart block. Common, especially with inferior myocardial infarction. Often resolve spontaneously if onset <24 h.
    *   **3 days:**
        *   *Cardiogenic shock:* Strongly dependent on infarct size; 5-6% of patients with STEMI.
        *   *Stroke:* Thromboembolic from PCI or hemorrhagic from antithrombotic therapy. Long-term risk in large anterior infarct, left ventricular aneurysm, or reduced left ventricular ejection fraction.
        *   *Ischemic MR / papillary muscle rupture:* Posterior papillary muscle most often; supplied by dominant artery. Characteristic murmur of MR may be absent.
        *   *Ventricular septal rupture:* Most common with anterior myocardial infarction. Holosystolic murmur at LSB (Left Sternal Border).
    *   **2 weeks:**
        *   *LV free wall rupture:* Persistent STE, upright T-waves, reversal of initially inverted T-waves. >50% mortality even with surgery.
        *   *Pericarditis (Dressler syndrome):* Autoimmune reaction; more common in large infarcts. Persistent STE, PR depression, may have a friction rub.

#### หน้า 38: Figure 12-18 Gross Pathology of MI Complications
*(สไลด์แสดงภาพถ่ายหัวใจจริงที่เกิดภาวะแทรกซ้อนรุนแรงรูปแบบต่างๆ)*

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 38)

> 🖼️ **คำอธิบายภาพ หน้า 38:**
> ภาพถ่ายทางพยาธิวิทยาแสดงภาวะแทรกซ้อนหลังเกิดกล้ามเนื้อหัวใจตาย:
> *   **ภาพ A (Anterior myocardial rupture):** แสดงรอยฉีกขาดทะลุสีแดงเข้มที่บริเวณผนังหน้าของหัวใจห้องล่างซ้าย (ลูกศรชี้) นำไปสู่ภาวะเลือดออกในช่องเยื่อหุ้มหัวใจ (Hemopericardium)
> *   **ภาพ B (Rupture of ventricular septum):** แสดงรอยทะลุเชื่อมระหว่างหัวใจห้องล่างซ้ายและขวาบริเวณผนังกั้นห้องหัวใจ (ลูกศรชี้) เกิดเป็น Left-to-right shunt
> *   **ภาพ C (Rupture of papillary muscle):** แสดงเส้นใยกล้ามเนื้อยึดลิ้นหัวใจ (Papillary muscle) ขาดออกจากกันโดยสมบูรณ์ ทำให้ลิ้นหัวใจ Mitral กะพือและรั่วรุนแรง
> *   **ภาพ D (Fibrinous pericarditis):** ผิวเยื่อหุ้มหัวใจชั้นนอกมีลักษณะขรุขระสีแดงเข้มจากการอักเสบและมีเส้นใยไฟบรินเกาะหนาตัว (Bread-and-butter appearance)
> *   **ภาพ E (Infarct expansion & Mural thrombus):** ผนังหัวใจส่วนปลายบางลงและโป่งออก ร่วมกับมีลิ่มเลือดสีแดงดำขนาดใหญ่ (Mural thrombus) เกาะติดอยู่ภายในห้องหัวใจ (ลูกศรชี้) ซึ่งเสี่ยงต่อการหลุดลอยไปอุดตันที่สมอง
> *   **ภาพ F (LV Aneurysm):** หัวใจห้องล่างซ้ายเกิดการโป่งพองเป็นถุงผนังบางสีขาวซีดจากเนื้อเยื่อพังผืด (ลูกศรชี้) ทำให้หัวใจบีบตัวไม่มีประสิทธิภาพ

### 🧠 กลไกและเหตุผลทางการแพทย์
1. **กลไกการเกิด Cardiogenic Shock**: เกิดเมื่อพื้นที่กล้ามเนื้อหัวใจตายมีขนาดกว้างใหญ่ **มากกว่า 40%** ของหัวใจห้องล่างซ้าย ทำให้แรงบีบตัวลดลงอย่างรุนแรง (Impaired contractility) ส่งผลให้ปริมาตรเลือดที่ส่งออกจากหัวใจต่อนาที (Cardiac Output) ลดลง ความดันโลหิตตก เลือดไปเลี้ยงอวัยวะต่างๆ รวมถึงหลอดเลือดหัวใจเองลดลง ยิ่งซ้ำเติมให้เกิดหัวใจขาดเลือดรุนแรงขึ้นเป็นวงจรอุบาทว์ (Vicious cycle)
2. **ทำไมกล้ามเนื้อยึดลิ้นหัวใจฝั่ง Posteromedial จึงขาดบ่อยกว่า?**:
    * **Anterolateral papillary muscle** ได้รับเลือดมาเลี้ยงจากหลอดเลือด 2 เส้นคู่กันคือ LAD และ LCX (Dual blood supply) จึงทนทานต่อการขาดเลือดได้ดีกว่า
    * **Posteromedial papillary muscle** ได้รับเลือดมาเลี้ยงจากหลอดเลือดเพียงเส้นเดียวคือ PDA (Single blood supply จาก RCA หรือ LCX ขึ้นกับความเด่นของหลอดเลือด) เมื่อเกิดการอุดตันของหลอดเลือดเส้นนี้ จึงเกิดการขาดเลือดและฉีกขาดได้ง่ายกว่ามาก นำไปสู่ภาวะลิ้นหัวใจรั่วเฉียบพลัน (Acute Mitral Regurgitation)

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* **ภาวะแทรกซ้อนทางไฟฟ้า (Arrhythmias)**: เป็นสาเหตุการเสียชีวิตที่พบบ่อยที่สุดใน **4 ชั่วโมงแรก** หลังเกิด MI โดยเฉพาะหัวใจเต้นพริ้ว (Ventricular Fibrillation - VF)
* **ภาวะแทรกซ้อนทางกลศาสตร์ (Mechanical complications)**: มักเกิดในช่วง **3-14 วัน** หลังเกิด MI ได้แก่:
    * **Free wall rupture** → เลือดคั่งในช่องเยื่อหุ้มหัวใจ บีบรัดหัวใจจนหยุดเต้น (**Cardiac tamponade**)
    * **Papillary muscle rupture** → ลิ้นหัวใจรั่วรุนแรงเฉียบพลัน (**Acute MR**) เกิดน้ำท่วมปอดรุนแรง
    * **Septal rupture** → ผนังกั้นห้องหัวใจทะลุ เกิดเสียงฟู่ชนิด Holosystolic murmur
* **Dressler Syndrome**: คือภาวะเยื่อหุ้มหัวใจอักเสบจากปฏิกิริยาภูมิคุ้มกันตัวเอง มักเกิดตามหลัง MI ประมาณ **2 สัปดาห์ถึงหลายเดือน**

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
✅ ข้อมูลสอดคล้องกับพยาธิวิทยาและแนวทางเวชปฏิบัติโรคหัวใจมาตรฐาน

---

## Section 10: Sudden Cardiac Death (SCD) — หน้า 39–42

> 📍 **ตำแหน่งในเอกสาร:** หน้า 39–42

### เนื้อหาจากสไลด์

#### หน้า 39: Sudden Cardiac Death (SCD)
*   Defined as **unexpected death from cardiac causes** early after symptom onset (usually within 1 hour) or without the onset of symptoms.
*   Is also known as a **"Massive Heart Attack"** in which the heart converts from sinus rhythm to ventricular fibrillation.

#### หน้า 40: Non-atherosclerotic Causes of SCD
*   Non-atherosclerotic causes of SCD become increasingly probable in decreasing age patient:
    *   Congenital structural or coronary arterial abnormalities
    *   Aortic valve stenosis
    *   Mitral valve prolapse
    *   Myocarditis
    *   Dilated or hypertrophic cardiomyopathy
    *   Pulmonary hypertension
    *   Hereditary or acquired abnormalities of the cardiac conduction system
    *   Isolated hypertrophy, hypertensive or unknown cause.

#### หน้า 41: Mechanism of SCD
*   The mechanism of SCD is most often a **lethal arrhythmia** (e.g., asystole, ventricular fibrillation).
*   **Fatal arrhythmia** is triggered by electrical irritability of myocardium that may be distant from the conduction system, induced by ischemia.
*   The prognosis of patients vulnerable to SCD, especially those with chronic IHD, is markedly improved by implantation of an **automatic cardioverter defibrillator (ICD)**, which senses and electrically counteracts an episode of ventricular fibrillation.

#### หน้า 42: Figure 12-19 Causes and Outcomes of Ischemic Heart Disease
*(สไลด์แสดงแผนผังความเชื่อมโยงระหว่างโรคหลอดเลือดหัวใจ, กล้ามเนื้อหัวใจตาย, หัวใจล้มเหลว และการเสียชีวิตเฉียบพลัน)*

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 42)

> 🖼️ **คำอธิบายภาพ หน้า 42:**
> แผนผังแสดงความสัมพันธ์เชิงพยาธิวิทยาของโรคหลอดเลือดหัวใจ (Coronary Artery Disease):
> 1.  **Coronary Artery Disease** สามารถนำไปสู่:
>     *   *Myocardial ischemia* (กล้ามเนื้อหัวใจขาดเลือดชั่วคราว)
>     *   *Acute plaque change / coronary thrombosis* (คราบไขมันแตกและมีลิ่มเลือดอุดตันเฉียบพลัน)
> 2.  ทั้งสองภาวะนำไปสู่ **Myocardial Infarction** (กล้ามเนื้อหัวใจตาย) ร่วมกับการสูญเสียกล้ามเนื้อและเกิดหัวใจเต้นผิดจังหวะ (Arrhythmias)
> 3.  หลังเกิด MI จะเกิดกระบวนการ:
>     *   *Infarct healing* (การซ่อมแซมแผลเป็น)
>     *   *Ventricular remodeling* (การปรับเปลี่ยนโครงสร้างหัวใจห้องล่าง)
>     *   *Hypertrophy, dilation of viable muscle* (กล้ามเนื้อหัวใจส่วนที่เหลือโตและขยายขนาดเพื่อชดเชย)
> 4.  กระบวนการเหล่านี้ส่งผลให้เกิด **Chronic Ischemic Heart Disease (IHD)** และพัฒนาต่อไปเป็น **Congestive Heart Failure** (ภาวะหัวใจล้มเหลว)
> 5.  ผู้ป่วยในทุกระยะ (ตั้งแต่ขาดเลือดเฉียบพลัน, กล้ามเนื้อหัวใจตาย, หรือหัวใจล้มเหลวเรื้อรัง) มีความเสี่ยงที่จะเกิด **Sudden Cardiac Death** (การเสียชีวิตเฉียบพลัน) ได้ตลอดเวลาจากภาวะหัวใจเต้นผิดจังหวะรุนแรง

### 🧠 กลไกและเหตุผลทางการแพทย์
* **กลไกการเกิด Ventricular Fibrillation (VF) จาก Ischemia**: เมื่อเซลล์กล้ามเนื้อหัวใจขาดเลือดเฉียบพลัน จะเกิดความผิดปกติของปั๊มไอออนบนเยื่อหุ้มเซลล์ (เช่น `Na+/K+-ATPase` หยุดทำงาน) ส่งผลให้เกิดการสะสมของโพแทสเซียมภายนอกเซลล์ (Extracellular hyperkalemia) และแคลเซียมภายในเซลล์ ทำให้ศักย์ไฟฟ้าของเยื่อหุ้มเซลล์ในระยะพัก (Resting membrane potential) สูงขึ้น การนำไฟฟ้าช้าลง และระยะดื้อยา (Refractory period) ของเซลล์แต่ละบริเวณไม่เท่ากัน (Dispersion of refractoriness) เอื้อให้เกิดวงจรไฟฟ้าหมุนวน (**Re-entry circuit**) ซึ่งเป็นจุดเริ่มต้นของภาวะหัวใจเต้นพริ้ว (VF) หัวใจจะไม่สามารถบีบตัวส่งเลือดไปเลี้ยงสมองได้ ทำให้หมดสติในไม่กี่วินาทีและเสียชีวิตหากไม่ได้รับการช็อกไฟฟ้าหัวใจ (Defibrillation) ทันเวลา

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* **Sudden Cardiac Death (SCD)** คือการเสียชีวิตอย่างกะทันหันจากโรคหัวใจ โดยมักเสียชีวิตภายใน **1 ชั่วโมง** หลังเริ่มมีอาการ หรือเสียชีวิตโดยไม่มีอาการเตือนล่วงหน้า
* สาเหตุหลักของ SCD ในผู้ใหญ่วัยกลางคนขึ้นไปคือ **Atherosclerosis** แต่ในคนอายุน้อยมักเกิดจากสาเหตุอื่น เช่น **กล้ามเนื้อหัวใจหนาตัวผิดปกติ (Hypertrophic Cardiomyopathy)**, หัวใจอักเสบ (Myocarditis), หรือความผิดปกติของระบบนำไฟฟ้าหัวใจแต่กำเนิด
* กลไกการเสียชีวิตที่พบบ่อยที่สุดคือ **Ventricular Fibrillation (VF)** ซึ่งสามารถป้องกันและรักษาได้ด้วยการใส่เครื่องช็อกไฟฟ้าหัวใจอัตโนมัติ (**ICD**)

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
✅ ข้อมูลสอดคล้องกับแนวทางเวชปฏิบัติสากล (*AHA/ACC Guidelines for Management of Patients with Ventricular Arrhythmias and the Prevention of Sudden Cardiac Death*)

---

## Section 11: Treatment & Management of Ischemic Heart Disease — หน้า 43–46

> 📍 **ตำแหน่งในเอกสาร:** หน้า 43–46

### เนื้อหาจากสไลด์

#### หน้า 43: Treatment: PCI and CABG Diagrams
*(สไลด์แสดงภาพขั้นตอนการทำสวนหัวใจขยายหลอดเลือด และการผ่าตัดบายพาสหลอดเลือดหัวใจ)*

#### หน้า 44: Immediate Care & Reperfusion Therapy
*   **Immediate Care:**
    *   **Aspirin administration:** Aspirin is given as soon as possible unless contraindicated, to reduce blood clotting.
    *   **Nitroglycerin (nitrate):** Used for chest pain relief unless contraindicated.
    *   **Oxygen:** Administered if there are signs of hypoxia or respiratory distress.
    *   **Analgesia:** Morphine is used to manage severe chest pain.
    *   **Antiplatelet therapy:** A P2Y12 inhibitor is often given in addition to aspirin.
    *   **Anticoagulation:** Medications such as heparin are used to prevent further clotting.
*   **Reperfusion Therapy (for STEMI):**
    *   **1. Percutaneous Coronary Intervention (PCI):** Preferred if it can be performed within 90 minutes of first medical contact.
    *   **2. Thrombolysis:** Considered if PCI is not available within the recommended time frame.

#### หน้า 45: Management of Ischemic Heart Disease (Lifestyle)
*   **Management of Ischemic Heart Disease:**
    *   **Lifestyle:**
        *   Diet
        *   Exercise Preventive treatment
        *   Low-fat, low-cholesterol diet
        *   Cessation of smoking

#### หน้า 46: Figure 7 Recommended Nutrition
*(สไลด์แสดงภาพคำนาแนะนำการเลือกรับประทานอาหารเพื่อสุขภาพหัวใจ)*

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 43, 46)

> 🖼️ **คำอธิบายภาพ หน้า 43:**
> *   **ภาพบนซ้ายและกลาง:** แสดงขั้นตอนการทำ **PCI (Percutaneous Coronary Intervention)** หรือการทำบอลลูนขยายหลอดเลือด โดยการสอดสายสวน (Catheter) เข้าทางหลอดเลือดแดงที่ขาหนีบหรือข้อมือ วิ่งย้อนขึ้นไปจนถึงหลอดเลือดหัวใจที่ตีบ จากนั้นใช้ลวดนำทาง (Guide wire) ผ่านรอยตีบ นำบอลลูนไปพองขยายคราบไขมัน และวางขดลวดค้ำยัน (Stent) เพื่อถ่างขยายหลอดเลือดให้เลือดไหลผ่านได้สะดวก
> *   **ภาพล่าง:** แสดงการผ่าตัดทำทางเบี่ยงหลอดเลือดหัวใจ หรือ **CABG (Coronary Artery Bypass Graft)** โดยการนำหลอดเลือดดำจากขา (Saphenous vein) หรือหลอดเลือดแดงจากผนังหน้าอกด้านใน (Internal mammary artery) มาเย็บต่อข้ามผ่านจุดที่อุดตันเพื่อทำทางเดินเลือดใหม่ แบ่งเป็น Single (ต่อ 1 เส้น), Double (2 เส้น), Triple (3 เส้น), และ Quadruple (4 เส้น)

> 🖼️ **คำอธิบายภาพ หน้า 46:**
> แผนภาพคำแนะนำด้านโภชนาการเพื่อป้องกันโรคหัวใจ (Recommended Nutrition):
> *   **CHOOSE THESE (ลูกศรสีเขียวชี้ขึ้น - ควรเลือกทาน):** ผัก, ผลไม้, ถั่วเมล็ดแห้ม, ธัญพืชไม่ขัดสี, โปรตีนไขมันต่ำ, คาร์โบไฮเดรตเชิงซ้อน, ใยอาหาร, ไขมันไม่อิ่มตัวเชิงเดี่ยว (เช่น น้ำมันมะกอก), ไขมันไม่อิ่มตัวเชิงซ้อน (เช่น ปลาแซลมอน)
> *   **INSTEAD OF THESE (ลูกศรสีเหลืองชี้ลง - ควรลดละเลี่ยง):** ไขมันอิ่มตัว, โซเดียมในอาหาร, เนื้อสัตว์แปรรูป (เช่น ไส้กรอก), คาร์โบไฮเดรตขัดสี (เช่น ข้าวขาว), เครื่องดื่มเติมน้ำตาล, เครื่องดื่มแอลกอฮอล์
> *   **AVOID TRANS FAT (สัญลักษณ์ห้ามสีแดง - ห้ามทานเด็ดขาด):** เบเกอรี่อบสำเร็จ, อาหารทอดที่ใช้น้ำมันเติมไฮโดรเจน (Hydrogenated oil/shortening)

### 🧠 กลไกและเหตุผลทางการแพทย์
1. **กลไกของยาในกลุ่ม Immediate Care (MONA + GAP)**:
    * **Aspirin:** ยับยั้งเอนไซม์ Cyclooxygenase-1 (COX-1) อย่างถาวร ทำให้เกล็ดเลือดไม่สามารถสร้าง Thromboxane A2 ได้ จึงช่วยยับยั้งการเกาะกลุ่มของเกล็ดเลือดเพิ่มเติม
    * **Nitroglycerin:** เปลี่ยนเป็น Nitric Oxide (NO) กระตุ้นการสร้าง cGMP ทำให้กล้ามเนื้อเรียบของหลอดเลือดดำขยายตัว (Venodilation) ส่งผลให้เลือดไหลกลับเข้าหัวใจลดลง (Decrease Preload) ช่วยลดภาระงานและความต้องการออกซิเจนของหัวใจ
    * **Morphine:** นอกจากแก้ปวดรุนแรงแล้ว ยังมีฤทธิ์ขยายหลอดเลือดดำ ช่วยลด Preload และลดการทำงานของระบบประสาทซิมพาเทติก ช่วยลดความดันโลหิตและอัตราการเต้นของหัวใจ
    * **Heparin:** จับกับ Antithrombin III เพื่อยับยั้งการทำงานของ Thrombin (Factor IIa) และ Factor Xa ป้องกันไม่ให้ลิ่มเลือดก่อตัวเพิ่มขึ้น
2. **ทำไมต้องเลี่ยง Trans Fat?**: ไขมันทรานส์จะไปเพิ่มระดับ LDL-Cholesterol (ไขมันเลว) และลดระดับ HDL-Cholesterol (ไขมันดี) ในเลือด อีกทั้งยังกระตุ้นให้เกิดการอักเสบของระบบหลอดเลือด (Systemic inflammation) และ Endothelial dysfunction ซึ่งเร่งการดำเนินไปของโรคหลอดเลือดแดงแข็งอย่างรวดเร็ว

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* **การรักษาเบื้องต้นทันทีเมื่อสงสัยภาวะกล้ามเนื้อหัวใจขาดเลือดเฉียบพลัน**: ประกอบด้วยการเคี้ยว **Aspirin**, อมยาขยายหลอดเลือดใต้ลิ้น (**Nitroglycerin**), ให้ยาแก้ปวด **Morphine**, และให้ยาต้านเกล็ดเลือดตัวที่สองร่วมกับยาต้านการแข็งตัวของเลือด (Heparin)
* **การเปิดหลอดเลือด (Reperfusion)**: ในผู้ป่วย STEMI วิธีที่ดีที่สุดคือการสวนหัวใจขยายหลอดเลือดเฉียบพลัน (**Primary PCI**) ภายใน **90 นาที** หากทำไม่ได้ในเกณฑ์เวลา ให้พิจารณาให้ยาละลายลิ่มเลือด (**Thrombolysis**) แทน
* **การป้องกันระยะยาว**: เน้นการปรับเปลี่ยนพฤติกรรม ได้แก่ การหยุดสูบบุหรี่เด็ดขาด, ออกกำลังกายสม่ำเสมอ, และทานอาหารที่มีไขมันอิ่มตัวต่ำ เลี่ยงไขมันทรานส์ (Trans fat)

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
* ‼️ **ในสไลด์ (หน้า 44):** "Oxygen: Administered if there are signs of hypoxia or respiratory distress."
* **ตามแหล่งอ้างอิง:** แนวทางเวชปฏิบัติปัจจุบันของ *AHA/ACC* และ *ESC* แนะนำชัดเจนว่า **ห้ามให้ Oxygen เป็นกิจวัตร (Routine)** ในผู้ป่วย ACS ทุกราย ให้เฉพาะผู้ป่วยที่มีภาวะ Hypoxia จริงๆ เท่านั้น (ระดับความอิ่มตัวของออกซิเจนในเลือด **SpO₂ < 90%** หรือมีภาวะหายใจลำบาก) เนื่องจากออกซิเจนที่มากเกินไป (Hyperoxia) อาจทำให้หลอดเลือดหัวใจหดตัว (Coronary vasoconstriction) และเพิ่มการสร้างอนุมูลอิสระ (Reactive Oxygen Species) ซึ่งส่งผลเสียต่อกล้ามเนื้อหัวใจเพิ่มขึ้น
* **แหล่งอ้างอิง:** *2023 ESC Guidelines for the management of acute coronary syndromes* — https://academic.oup.com/eurheartj/article/44/38/3720/7256543

---

## Section 12: Chronic Ischemic Heart Disease (CIHD) — หน้า 47–49

> 📍 **ตำแหน่งในเอกสาร:** หน้า 47–49

### เนื้อหาจากสไลด์

#### หน้า 47: Chronic Ischemic Heart Disease (CIHD)
*   Is used here to describe the cardiac findings in patients, often but not exclusively elderly, who develop **progressive heart failure** as a consequence of ischemic myocardial damage.
*   The term **ischemic cardiomyopathy** is often used by clinicians to describe Chronic ischemic heart disease (CIHD).

#### หน้า 48: Clinical Diagnosis of CIHD
*   Is made by the **insidious onset of CHF** (Congestive Heart Failure) in patients who have had past episodes of MI or anginal attacks.
*   In some individuals, however, progressive myocardial damage is entirely **silent**, and heart failure is the first indication of CIHD.

#### หน้า 49: End Slide
*   **END**
*(สไลด์แสดงภาพลูกแมวสีส้มตากลมโตเพื่อจบการนำเสนอ)*

---

### 🖼️ การจัดการหน้ารูปภาพ (หน้า 49)

> 🖼️ **คำอธิบายภาพ หน้า 49:**
> ภาพปิดท้ายการนำเสนอ (End slide) แสดงรูปภาพลูกแมวสีส้มขนฟูตากลมโตสีฟ้าอมเขียวจ้องมองมาที่กล้องอย่างน่ารัก เพื่อสร้างบรรยากาศผ่อนคลายหลังจบเนื้อหาทางวิชาการที่หนักหน่วง

### 🧠 กลไกและเหตุผลทางการแพทย์
* **กลไกการเกิด Ischemic Cardiomyopathy**: เกิดจากการสูญเสียกล้ามเนื้อหัวใจที่ทำงานได้จริงไปทีละน้อยจากการเกิดกล้ามเนื้อหัวใจตายในอดีต (Past MI) หรือจากการขาดเลือดเรื้อรังซ้ำๆ (Chronic sublethal ischemia) ส่งผลให้กล้ามเนื้อหัวใจส่วนที่เหลือต้องทำงานหนักขึ้นเพื่อชดเชย เกิดกระบวนการ **Ventricular Remodeling** ผนังหัวใจจะหนาตัวขึ้นและห้องหัวใจจะค่อยๆ ขยายขนาดใหญ่ขึ้น (Dilation) จนในที่สุดกล้ามเนื้อหัวใจจะล้าและสูญเสียความสามารถในการบีบตัวส่งเลือด (Systolic dysfunction) นำไปสู่ภาวะหัวใจล้มเหลวเรื้อรัง (Congestive Heart Failure)

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
* **Chronic Ischemic Heart Disease (CIHD)** หรือเรียกอีกชื่อว่า **Ischemic Cardiomyopathy** คือภาวะหัวใจล้มเหลวเรื้อรังที่เป็นผลตามมาจากความเสียหายของกล้ามเนื้อหัวใจจากการขาดเลือดในอดีต
* การวินิจฉัยมักพบในผู้ป่วยที่มีประวัติเป็นโรคกล้ามเนื้อหัวใจตาย (MI) หรือเจ็บหน้าอกมาก่อน แล้วค่อยๆ พัฒนาอาการของภาวะหัวใจล้มเหลว (เช่น เหนื่อยง่าย นอนราบไม่ได้ ขาบวม) อย่างช้าๆ
* ในผู้ป่วยบางราย (โดยเฉพาะผู้ป่วยเบาหวานหรือผู้สูงอายุ) การขาดเลือดอาจไม่มีอาการเจ็บหน้าอกเตือนเลย (**Silent ischemia**) และมาพบแพทย์ด้วยอาการหัวใจล้มเหลวเป็นอาการแรก

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
✅ ข้อมูลสอดคล้องกับแนวทางเวชปฏิบัติและตำราอายุรศาสตร์มาตรฐาน (*Harrison's Principles of Internal Medicine*)
```