export type HighlightReference = {
  name: string;
  url: string;
};

export type DayHighlightItem = {
  ayahRef: string;
  themeType: "Dua" | "Famous Ayah";
  shortTitle: string;
  whyNotable: string[];
  summary: string;
  keyTakeaway: string;
  references: HighlightReference[];
};

export type DayCorpusSummary = {
  title: string;
  summary: string;
  themes: string[];
};

export const dayHighlights: Record<number, DayHighlightItem[]> = {
  1: [
    {
      ayahRef: "2:2-5",
      themeType: "Famous Ayah",
      shortTitle: "Traits of the Muttaqun",
      whyNotable: [
        "Among the most cited opening ayat in Al-Baqarah for defining taqwa.",
        "Frequently used in classes to frame practical signs of sincere faith.",
      ],
      summary:
        "These ayat present the Quran as guidance for the God-conscious and describe foundational traits: belief in the unseen, prayer, charity, trust in revelation, and certainty in the Hereafter.",
      keyTakeaway: "Measure iman by worship, obedience, and consistency.",
      references: [
        { name: "Quran 2:2-5", url: "https://quran.com/2:2-5" },
        { name: "Ibn Kathir Tafsir (2:2)", url: "https://quran.com/en/2:2/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:21-22",
      themeType: "Famous Ayah",
      shortTitle: "Universal Call to Worship Allah",
      whyNotable: [
        "A widely quoted tawhid passage addressed to all humanity.",
        "Commonly used in da'wah and foundational aqidah teaching.",
      ],
      summary:
        "Allah calls all people to worship Him alone and reminds them of creation and provision. The ayah establishes gratitude and worship as inseparable.",
      keyTakeaway: "Let awareness of Allah's favors deepen worship.",
      references: [
        { name: "Quran 2:21-22", url: "https://quran.com/2:21-22" },
        { name: "Ibn Kathir Tafsir (2:21)", url: "https://quran.com/en/2:21/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:23-24",
      themeType: "Famous Ayah",
      shortTitle: "The Quranic Challenge",
      whyNotable: [
        "One of the most famous proof passages on the Quran's inimitability.",
        "Repeatedly referenced in discussions of revelation and certainty.",
      ],
      summary:
        "Those who doubt revelation are challenged to produce even one surah like it. The passage combines an evidentiary challenge with a serious warning.",
      keyTakeaway: "Approach the Quran as evidence and guidance.",
      references: [
        { name: "Quran 2:23-24", url: "https://quran.com/2:23-24" },
        { name: "Ibn Kathir Tafsir (2:23)", url: "https://quran.com/en/2:23/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:74",
      themeType: "Famous Ayah",
      shortTitle: "Do Not Let the Heart Harden",
      whyNotable: [
        "A well-known warning ayah about spiritual hardening.",
        "Frequently cited in reminders on repentance and humility.",
      ],
      summary:
        "The ayah warns that hearts can harden even after clear signs. It calls believers to remain soft-hearted before Allah through remembrance and obedience.",
      keyTakeaway: "Guard the heart before spiritual numbness settles in.",
      references: [
        { name: "Quran 2:74", url: "https://quran.com/2:74" },
        { name: "Ibn Kathir Tafsir (2:74)", url: "https://quran.com/en/2:74/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:121",
      themeType: "Famous Ayah",
      shortTitle: "Reciting the Book As It Should Be Recited",
      whyNotable: [
        "A famous ayah on sincere engagement with the Quran.",
        "Used to distinguish living the Quran from reciting without practice.",
      ],
      summary:
        "This ayah praises those who recite the Book with its due right and truly believe in it. It links recitation to commitment and practice.",
      keyTakeaway: "Read the Quran to transform life, not only to complete pages.",
      references: [
        { name: "Quran 2:121", url: "https://quran.com/2:121" },
        { name: "Ibn Kathir Tafsir (2:121)", url: "https://quran.com/en/2:121/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:124",
      themeType: "Famous Ayah",
      shortTitle: "Ibrahim and Leadership Through Obedience",
      whyNotable: [
        "A major, widely quoted ayah about leadership after trial.",
        "Clarifies covenant is tied to righteousness, not lineage alone.",
      ],
      summary:
        "After Ibrahim fulfilled divine tests, Allah granted him leadership. The ayah establishes that divine covenant is not for wrongdoers.",
      keyTakeaway: "Leadership in deen is earned by obedience and justice.",
      references: [
        { name: "Quran 2:124", url: "https://quran.com/2:124" },
        { name: "Ibn Kathir Tafsir (2:124)", url: "https://quran.com/en/2:124/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  2: [
    {
      ayahRef: "2:143",
      themeType: "Famous Ayah",
      shortTitle: "A Middle Nation",
      whyNotable: [
        "A defining and widely cited ayah for Muslim identity and balance.",
        "Frequently referenced in khutbahs and educational settings.",
      ],
      summary:
        "This ayah describes the Ummah as a balanced nation entrusted with witness-bearing. It frames communal identity through responsibility and justice.",
      keyTakeaway: "Balance in deen is a trust, not a slogan.",
      references: [
        { name: "Quran 2:143", url: "https://quran.com/2:143" },
        { name: "Ibn Kathir Tafsir (2:143)", url: "https://quran.com/en/2:143/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:177",
      themeType: "Famous Ayah",
      shortTitle: "Righteousness Beyond Formality",
      whyNotable: [
        "A highly famous summary ayah of belief, ethics, and worship.",
        "Commonly used to teach holistic righteousness in Islam.",
      ],
      summary:
        "The ayah defines righteousness as sound belief, worship, generosity, covenant-keeping, and patience. It rejects reducing deen to outward form only.",
      keyTakeaway: "Birr combines creed, worship, and character.",
      references: [
        { name: "Quran 2:177", url: "https://quran.com/2:177" },
        { name: "Ibn Kathir Tafsir (2:177)", url: "https://quran.com/en/2:177/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:183",
      themeType: "Famous Ayah",
      shortTitle: "Fasting Prescribed for Taqwa",
      whyNotable: [
        "The foundational and most-recited ayah introducing Ramadan fasting.",
        "Universally referenced each Ramadan for intention and purpose.",
      ],
      summary:
        "Allah prescribes fasting as for previous communities and states taqwa as its objective. It frames fasting as spiritual discipline, not only abstinence.",
      keyTakeaway: "Fast to reform the heart and increase taqwa.",
      references: [
        { name: "Quran 2:183", url: "https://quran.com/2:183" },
        { name: "Ibn Kathir Tafsir (2:183)", url: "https://quran.com/en/2:183/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:186",
      themeType: "Dua",
      shortTitle: "Allah Is Near and Responds",
      whyNotable: [
        "One of the most famous ayat on dua and divine response.",
        "Widely recited in Ramadan reminders and supplication guidance.",
      ],
      summary:
        "Allah declares His nearness and His response to those who call on Him sincerely. The ayah links answered dua with responding to Allah in obedience.",
      keyTakeaway: "Call on Allah often and live by His guidance.",
      references: [
        { name: "Quran 2:186", url: "https://quran.com/2:186" },
        { name: "Ibn Kathir Tafsir (2:186)", url: "https://quran.com/en/2:186/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:201",
      themeType: "Dua",
      shortTitle: "Rabbana Atina",
      whyNotable: [
        "Among the most famous and widely memorized Quranic duas.",
        "Balances dunya and akhirah in a concise, complete supplication.",
      ],
      summary:
        "This dua asks Allah for goodness in this life, goodness in the next, and protection from the Fire. It teaches balanced aspiration and dependence on Allah.",
      keyTakeaway: "Ask for complete goodness, not one-sided success.",
      references: [
        { name: "Quran 2:201", url: "https://quran.com/2:201" },
        { name: "Ibn Kathir Tafsir (2:201)", url: "https://quran.com/en/2:201/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:250",
      themeType: "Dua",
      shortTitle: "Dua for Firmness and Victory",
      whyNotable: [
        "A famous dua recited in moments of fear and challenge.",
        "Combines patience, steadfastness, and reliance on Allah.",
      ],
      summary:
        "Believers facing a stronger force asked Allah for patience, firmness, and victory. The ayah models spiritual composure under pressure.",
      keyTakeaway: "In pressure, begin with dua and steadfastness.",
      references: [
        { name: "Quran 2:250", url: "https://quran.com/2:250" },
        { name: "Ibn Kathir Tafsir (2:250)", url: "https://quran.com/en/2:250/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  3: [
    {
      ayahRef: "2:255",
      themeType: "Famous Ayah",
      shortTitle: "Ayat al-Kursi",
      whyNotable: [
        "Among the most well-known and frequently recited ayat in the Quran.",
        "Widely memorized and used in daily adhkar for protection and reflection.",
      ],
      summary:
        "Ayat al-Kursi declares Allah's perfect life, sustaining power, and complete authority over the heavens and earth. It is a central ayah for tawhid and reliance.",
      keyTakeaway: "Strengthen tawhid by reflecting on Allah's absolute sovereignty.",
      references: [
        { name: "Quran 2:255", url: "https://quran.com/2:255" },
        { name: "Ibn Kathir Tafsir (2:255)", url: "https://quran.com/en/2:255/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "2:285-286",
      themeType: "Dua",
      shortTitle: "The Closing Dua of Al-Baqarah",
      whyNotable: [
        "A famous closing passage that many Muslims recite nightly.",
        "Combines iman, obedience, repentance, and direct supplication.",
      ],
      summary:
        "The final ayat affirm belief in revelation and include a comprehensive dua asking for pardon, mercy, and help. They train the believer to end with humility and dependence on Allah.",
      keyTakeaway: "Close your worship with repentance and sincere dua.",
      references: [
        { name: "Quran 2:285-286", url: "https://quran.com/2:285-286" },
        { name: "Ibn Kathir Tafsir (2:286)", url: "https://quran.com/en/2:286/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "3:8",
      themeType: "Dua",
      shortTitle: "Rabbana La Tuzigh Qulubana",
      whyNotable: [
        "One of the most famous Quranic duas for steadfastness on guidance.",
        "Commonly recited in personal worship and community reminders.",
      ],
      summary:
        "Believers ask Allah not to let their hearts deviate after receiving guidance and to grant mercy from Him. The ayah emphasizes that firmness comes from Allah's favor.",
      keyTakeaway: "Ask Allah consistently for stability and mercy.",
      references: [
        { name: "Quran 3:8", url: "https://quran.com/3:8" },
        { name: "Ibn Kathir Tafsir (3:8)", url: "https://quran.com/en/3:8/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "3:26-27",
      themeType: "Famous Ayah",
      shortTitle: "Sovereignty Belongs to Allah",
      whyNotable: [
        "A highly cited passage on power, honor, and Allah's control of affairs.",
        "Frequently used to teach reliance beyond political or worldly shifts.",
      ],
      summary:
        "These ayat affirm that Allah grants and removes dominion, honors and humiliates, and controls life cycles in creation. They reset the believer's perspective on power and provision.",
      keyTakeaway: "Anchor your trust in Allah, not temporary worldly control.",
      references: [
        { name: "Quran 3:26-27", url: "https://quran.com/3:26-27" },
        { name: "Ibn Kathir Tafsir (3:26)", url: "https://quran.com/en/3:26/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "3:31",
      themeType: "Famous Ayah",
      shortTitle: "Following the Prophet as Proof of Love",
      whyNotable: [
        "A foundational ayah often cited to define sincere love of Allah.",
        "Links love of Allah directly to following the Sunnah.",
      ],
      summary:
        "Allah commands that true love is proven by following the Messenger. The ayah connects devotion to obedience and promises divine love and forgiveness.",
      keyTakeaway: "Show love of Allah through practical adherence to the Sunnah.",
      references: [
        { name: "Quran 3:31", url: "https://quran.com/3:31" },
        { name: "Ibn Kathir Tafsir (3:31)", url: "https://quran.com/en/3:31/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "3:92",
      themeType: "Famous Ayah",
      shortTitle: "Giving What You Love",
      whyNotable: [
        "A famous ayah defining real birr through meaningful sacrifice.",
        "Often referenced in lessons about charity, sincerity, and detachment.",
      ],
      summary:
        "This ayah teaches that true righteousness is not reached until one spends from what one loves. It calls for generosity that costs the ego, not only surplus giving.",
      keyTakeaway: "Give to Allah from what is valuable to you.",
      references: [
        { name: "Quran 3:92", url: "https://quran.com/3:92" },
        { name: "Ibn Kathir Tafsir (3:92)", url: "https://quran.com/en/3:92/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  4: [
    {
      ayahRef: "3:103",
      themeType: "Famous Ayah",
      shortTitle: "Hold Firmly to the Rope of Allah",
      whyNotable: [
        "A foundational and widely cited ayah on unity and avoiding division.",
        "Frequently recited in khutbahs and community reminders.",
      ],
      summary:
        "Allah commands believers to hold fast together to His guidance and not split into factions. The ayah frames unity as a mercy from Allah and a condition for communal strength.",
      keyTakeaway: "Protect unity by staying anchored to revelation.",
      references: [
        { name: "Quran 3:103", url: "https://quran.com/3:103" },
        { name: "Ibn Kathir Tafsir (3:103)", url: "https://quran.com/en/3:103/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "3:173",
      themeType: "Famous Ayah",
      shortTitle: "Hasbunallahu wa Ni'mal-Wakeel",
      whyNotable: [
        "One of the most famous Quranic expressions of tawakkul under threat.",
        "Commonly used in personal dua and collective reminders in hardship.",
      ],
      summary:
        "When believers were warned about danger, they answered with trust: Allah is sufficient for us and the best disposer of affairs. The ayah links courage to reliance on Allah, not to worldly numbers.",
      keyTakeaway: "Answer fear with tawakkul and principled resolve.",
      references: [
        { name: "Quran 3:173", url: "https://quran.com/3:173" },
        { name: "Ibn Kathir Tafsir (3:173)", url: "https://quran.com/en/3:173/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "3:190-191",
      themeType: "Famous Ayah",
      shortTitle: "Reflection on Creation and Constant Dhikr",
      whyNotable: [
        "A famous passage on contemplative worship and signs in creation.",
        "Widely cited in lessons on tafakkur, dhikr, and living intellect.",
      ],
      summary:
        "These ayat praise those who remember Allah in every posture and reflect deeply on the heavens and earth. True reflection leads to humility, worship, and purposeful action.",
      keyTakeaway: "Let reflection increase remembrance and obedience.",
      references: [
        { name: "Quran 3:190-191", url: "https://quran.com/3:190-191" },
        { name: "Ibn Kathir Tafsir (3:190)", url: "https://quran.com/en/3:190/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "3:193-194",
      themeType: "Dua",
      shortTitle: "Rabbana Innana Sami'na",
      whyNotable: [
        "A major Quranic dua sequence focused on forgiveness and steadfast reward.",
        "Frequently recited in night prayer and personal supplication.",
      ],
      summary:
        "Believers ask Allah for forgiveness, firmness with the righteous, and fulfillment of His promises. The dua combines iman, repentance, and hope in Allah's mercy.",
      keyTakeaway: "Pair belief with persistent dua and repentance.",
      references: [
        { name: "Quran 3:193-194", url: "https://quran.com/3:193-194" },
        { name: "Ibn Kathir Tafsir (3:193)", url: "https://quran.com/en/3:193/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "3:200",
      themeType: "Famous Ayah",
      shortTitle: "Steadfastness and Readiness",
      whyNotable: [
        "A renowned closing ayah of Aal-i-Imraan with a practical program for perseverance.",
        "Often quoted as a summary framework for sabr and taqwa.",
      ],
      summary:
        "Allah commands believers to persevere, outlast opposition in patience, remain prepared, and maintain taqwa. The ayah ends the surah with discipline-oriented spirituality.",
      keyTakeaway: "Victory grows from sabr, readiness, and taqwa.",
      references: [
        { name: "Quran 3:200", url: "https://quran.com/3:200" },
        { name: "Ibn Kathir Tafsir (3:200)", url: "https://quran.com/en/3:200/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "4:1",
      themeType: "Famous Ayah",
      shortTitle: "Taqwa and the Rights of Kinship",
      whyNotable: [
        "A highly cited opening ayah that frames social justice through taqwa.",
        "Commonly referenced in nikah sermons and family-rights reminders.",
      ],
      summary:
        "Allah calls humanity to revere Him, reminding them of shared origin and the sanctity of family ties. The ayah establishes social ethics on spiritual accountability.",
      keyTakeaway: "Build family and society on taqwa and responsibility.",
      references: [
        { name: "Quran 4:1", url: "https://quran.com/4:1" },
        { name: "Ibn Kathir Tafsir (4:1)", url: "https://quran.com/en/4:1/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  5: [
    {
      ayahRef: "4:28",
      themeType: "Famous Ayah",
      shortTitle: "Allah Intends Ease for You",
      whyNotable: [
        "A widely cited ayah that captures the principle of divine ease in the Shariah.",
        "Frequently referenced in reminders against spiritual excess and hardship culture.",
      ],
      summary:
        "Allah clarifies that His intent is to lighten burdens for believers, acknowledging human weakness. The ayah frames legal guidance with mercy and practical realism.",
      keyTakeaway: "Practice deen with sincerity and balance, not self-imposed hardship.",
      references: [
        { name: "Quran 4:28", url: "https://quran.com/4:28" },
        { name: "Ibn Kathir Tafsir (4:28)", url: "https://quran.com/en/4:28/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "4:32",
      themeType: "Dua",
      shortTitle: "Ask Allah from His Bounty",
      whyNotable: [
        "A key ayah for correcting envy and redirecting the heart toward dua.",
        "Commonly taught as a practical spiritual response to comparison.",
      ],
      summary:
        "The ayah forbids coveting what Allah has given others and instructs believers to ask Him from His bounty instead. It replaces jealousy with gratitude, effort, and dua.",
      keyTakeaway: "When tested by comparison, turn to Allah in dua.",
      references: [
        { name: "Quran 4:32", url: "https://quran.com/4:32" },
        { name: "Ibn Kathir Tafsir (4:32)", url: "https://quran.com/en/4:32/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  6: [
    {
      ayahRef: "5:2",
      themeType: "Famous Ayah",
      shortTitle: "Cooperate in Righteousness and Taqwa",
      whyNotable: [
        "One of the most cited Quranic principles for collective ethics and community conduct.",
        "Frequently used as a foundational ayah in dawah, masjid work, and social responsibility.",
      ],
      summary:
        "Allah commands believers to support one another in virtue and taqwa, and forbids cooperation in sin and transgression. It sets a clear framework for principled collaboration.",
      keyTakeaway: "Build community work on righteousness, not expediency.",
      references: [
        { name: "Quran 5:2", url: "https://quran.com/5:2" },
        { name: "Ibn Kathir Tafsir (5:2)", url: "https://quran.com/en/5:2/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "5:8",
      themeType: "Famous Ayah",
      shortTitle: "Justice Even Against Bias",
      whyNotable: [
        "A major and widely quoted ayah on principled justice.",
        "Regularly referenced in khutbahs and Islamic ethics discussions.",
      ],
      summary:
        "Believers are commanded to stand firmly for Allah in justice, without letting dislike of a people drive them to injustice. The ayah links justice directly to taqwa.",
      keyTakeaway: "Remain just even when emotions pull in the opposite direction.",
      references: [
        { name: "Quran 5:8", url: "https://quran.com/5:8" },
        { name: "Ibn Kathir Tafsir (5:8)", url: "https://quran.com/en/5:8/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "5:35",
      themeType: "Famous Ayah",
      shortTitle: "Seek Means to Allah and Strive",
      whyNotable: [
        "A very well-known ayah on drawing near to Allah through obedience and striving.",
        "Often cited in lessons on worship discipline and spiritual effort.",
      ],
      summary:
        "Allah commands taqwa, seeking nearness to Him, and striving in His cause for success. The ayah combines inward God-consciousness with outward effort.",
      keyTakeaway: "Taqwa grows through action, striving, and closeness to Allah.",
      references: [
        { name: "Quran 5:35", url: "https://quran.com/5:35" },
        { name: "Ibn Kathir Tafsir (5:35)", url: "https://quran.com/en/5:35/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "5:54",
      themeType: "Famous Ayah",
      shortTitle: "Allah Brings a People He Loves",
      whyNotable: [
        "A famous ayah describing the qualities of believers loved by Allah.",
        "Commonly quoted in reminders on sincerity, humility, and courage in deen.",
      ],
      summary:
        "Allah declares that if some turn away, He will bring a people He loves and who love Him: humble with believers, firm against opposition, and steadfast in striving for Allah.",
      keyTakeaway: "Seek to be among those defined by love of Allah and principled courage.",
      references: [
        { name: "Quran 5:54", url: "https://quran.com/5:54" },
        { name: "Ibn Kathir Tafsir (5:54)", url: "https://quran.com/en/5:54/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "5:78-79",
      themeType: "Famous Ayah",
      shortTitle: "Warning Against Normalizing Wrong",
      whyNotable: [
        "A well-known warning passage on leaving wrong uncorrected.",
        "Frequently taught in discussions of moral responsibility and communal reform.",
      ],
      summary:
        "The ayat condemn persistent disobedience and emphasize that people were blameworthy for failing to restrain one another from evil. It is a direct warning against passive acceptance of wrongdoing.",
      keyTakeaway: "Do not normalize sin; uphold sincere mutual accountability.",
      references: [
        { name: "Quran 5:78-79", url: "https://quran.com/5:78-79" },
        { name: "Ibn Kathir Tafsir (5:79)", url: "https://quran.com/en/5:79/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  7: [
    {
      ayahRef: "5:90",
      themeType: "Famous Ayah",
      shortTitle: "Avoid Intoxicants and Gambling",
      whyNotable: [
        "One of the most widely cited ayat in establishing the prohibition of intoxicants.",
        "Frequently referenced in reminders about spiritual purity and obedience.",
      ],
      summary:
        "This ayah commands believers to avoid intoxicants, gambling, idols, and divining arrows as filth from the work of Shaytan. It ties abstinence directly to success and spiritual protection.",
      keyTakeaway: "Leave what corrupts the heart to preserve taqwa and clarity.",
      references: [
        { name: "Quran 5:90", url: "https://quran.com/5:90" },
        { name: "Ibn Kathir Tafsir (5:90)", url: "https://quran.com/en/5:90/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "5:105",
      themeType: "Famous Ayah",
      shortTitle: "Guard Yourselves with Guidance",
      whyNotable: [
        "A famous ayah often quoted about personal responsibility in deen.",
        "Commonly discussed in tafsir lessons on balancing reform of self and society.",
      ],
      summary:
        "Believers are commanded to care for their own steadfastness while remaining on guidance. The ayah clarifies that ultimate return and judgment belong to Allah.",
      keyTakeaway: "Stay firm on guidance and accountability before Allah.",
      references: [
        { name: "Quran 5:105", url: "https://quran.com/5:105" },
        { name: "Ibn Kathir Tafsir (5:105)", url: "https://quran.com/en/5:105/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "6:79",
      themeType: "Famous Ayah",
      shortTitle: "Ibrahim's Declaration of Tawhid",
      whyNotable: [
        "A major, well-known ayah used to teach pure devotion and sincerity.",
        "Frequently cited in lessons on rejecting shirk and facing Allah alone.",
      ],
      summary:
        "Ibrahim declares that he has turned his face wholly to the One who created the heavens and the earth, in pure faith, free from shirk. The ayah is a timeless model of sincere monotheism.",
      keyTakeaway: "Orient your worship and life fully to Allah alone.",
      references: [
        { name: "Quran 6:79", url: "https://quran.com/6:79" },
        { name: "Ibn Kathir Tafsir (6:79)", url: "https://quran.com/en/6:79/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "6:103",
      themeType: "Famous Ayah",
      shortTitle: "Vision Cannot Encompass Allah",
      whyNotable: [
        "A foundational ayah in discussions of Allah's transcendence.",
        "Widely cited in creed-focused teaching and tafsir circles.",
      ],
      summary:
        "The ayah states that vision cannot encompass Allah, while He encompasses all vision; He is Subtle and All-Aware. It affirms divine majesty beyond created limitation.",
      keyTakeaway: "Know Allah through revelation with humility before His transcendence.",
      references: [
        { name: "Quran 6:103", url: "https://quran.com/6:103" },
        { name: "Ibn Kathir Tafsir (6:103)", url: "https://quran.com/en/6:103/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "6:108",
      themeType: "Famous Ayah",
      shortTitle: "Do Not Insult What Others Worship",
      whyNotable: [
        "A highly cited ayah for prophetic etiquette in da'wah and discourse.",
        "Frequently referenced to prevent harm and escalation in speech.",
      ],
      summary:
        "Believers are forbidden from insulting what others invoke besides Allah, lest people retaliate by insulting Allah in ignorance. The ayah sets a principle of wisdom, restraint, and foresight in religious engagement.",
      keyTakeaway: "Speak with wisdom and avoid speech that leads to greater harm.",
      references: [
        { name: "Quran 6:108", url: "https://quran.com/6:108" },
        { name: "Ibn Kathir Tafsir (6:108)", url: "https://quran.com/en/6:108/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  8: [
    {
      ayahRef: "6:151",
      themeType: "Famous Ayah",
      shortTitle: "Core Sacred Commandments",
      whyNotable: [
        "A highly cited set of foundational prohibitions and obligations.",
        "Often referenced as a concise framework of Quranic ethics.",
      ],
      summary:
        "This ayah gathers major commands around tawhid, family dignity, sanctity of life, and moral restraint. It presents core boundaries that protect faith and society.",
      keyTakeaway: "Hold to revealed boundaries as a path to taqwa.",
      references: [
        { name: "Quran 6:151", url: "https://quran.com/6:151" },
        { name: "Ibn Kathir Tafsir (6:151)", url: "https://quran.com/en/6:151/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "6:153",
      themeType: "Famous Ayah",
      shortTitle: "Follow the Straight Path",
      whyNotable: [
        "A well-known ayah on unity upon Allah's single path.",
        "Frequently cited against sectarian fragmentation and deviation.",
      ],
      summary:
        "Allah commands following His straight path and avoiding divergent ways that split believers from guidance. The ayah links unity to strict adherence to revelation.",
      keyTakeaway: "Stay on one revealed path and avoid divisive deviations.",
      references: [
        { name: "Quran 6:153", url: "https://quran.com/6:153" },
        { name: "Ibn Kathir Tafsir (6:153)", url: "https://quran.com/en/6:153/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "7:23",
      themeType: "Dua",
      shortTitle: "Dua of Adam and Hawwa",
      whyNotable: [
        "Among the most famous Quranic duas of repentance.",
        "Commonly memorized and recited when seeking forgiveness.",
      ],
      summary:
        "Adam and Hawwa confess their wrong and seek Allah's mercy, declaring that without His forgiveness they would be among the losers. It is a model of humble, direct repentance.",
      keyTakeaway: "Return quickly to Allah with honest confession and hope.",
      references: [
        { name: "Quran 7:23", url: "https://quran.com/7:23" },
        { name: "Ibn Kathir Tafsir (7:23)", url: "https://quran.com/en/7:23/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "7:43",
      themeType: "Dua",
      shortTitle: "Praise for Divine Guidance",
      whyNotable: [
        "A famous Quranic phrase of gratitude for being guided.",
        "Frequently quoted to express dependence on Allah's guidance.",
      ],
      summary:
        "The people of Paradise acknowledge they would never have been guided without Allah. The ayah teaches humility, gratitude, and recognition that guidance is a gift.",
      keyTakeaway: "Credit guidance to Allah and increase gratitude.",
      references: [
        { name: "Quran 7:43", url: "https://quran.com/7:43" },
        { name: "Ibn Kathir Tafsir (7:43)", url: "https://quran.com/en/7:43/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "7:89",
      themeType: "Dua",
      shortTitle: "Our Lord, Judge Between Us in Truth",
      whyNotable: [
        "A powerful prophetic supplication in conflict and trial.",
        "Used as a model dua for justice and truthful resolution.",
      ],
      summary:
        "Shu'ayb asks Allah to decide between peoples in truth, affirming that Allah is the best of judges. The ayah teaches turning disputes back to divine justice with trust.",
      keyTakeaway: "Seek resolution through truth and trust Allah's judgment.",
      references: [
        { name: "Quran 7:89", url: "https://quran.com/7:89" },
        { name: "Ibn Kathir Tafsir (7:89)", url: "https://quran.com/en/7:89/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  9: [
    {
      ayahRef: "7:89",
      themeType: "Dua",
      shortTitle: "Our Lord, Judge Between Us in Truth",
      whyNotable: [
        "A major Quranic dua for justice in times of dispute and pressure.",
        "Widely cited as a prophetic model of trust in Allah's judgment.",
      ],
      summary:
        "Shu'ayb asks Allah to decide between peoples in truth, affirming that Allah is the best of judges. The ayah teaches that resolution is sought through truth and divine justice, not ego or faction.",
      keyTakeaway: "In conflict, return to truth and trust Allah's just decree.",
      references: [
        { name: "Quran 7:89", url: "https://quran.com/7:89" },
        { name: "Ibn Kathir Tafsir (7:89)", url: "https://quran.com/en/7:89/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "7:151",
      themeType: "Dua",
      shortTitle: "Musa's Dua for Mercy and Reform",
      whyNotable: [
        "A famous prophetic supplication combining forgiveness and mercy.",
        "Frequently used to ask Allah for personal and communal rectification.",
      ],
      summary:
        "Musa asks Allah to forgive him and his brother and admit them into divine mercy. The dua joins repentance with concern for communal reform.",
      keyTakeaway: "Seek Allah's mercy while asking for reform in the Ummah.",
      references: [
        { name: "Quran 7:151", url: "https://quran.com/7:151" },
        { name: "Ibn Kathir Tafsir (7:151)", url: "https://quran.com/en/7:151/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "7:180",
      themeType: "Famous Ayah",
      shortTitle: "Call on Allah by His Most Beautiful Names",
      whyNotable: [
        "One of the most famous ayat connected to Asma' al-Husna.",
        "Commonly cited in worship, dua, and remembrance practice.",
      ],
      summary:
        "Allah declares that the most beautiful names belong to Him and commands believers to call on Him through them. The ayah anchors devotional life in reverence and correct belief.",
      keyTakeaway: "Deepen dua by calling Allah through His beautiful names.",
      references: [
        { name: "Quran 7:180", url: "https://quran.com/7:180" },
        { name: "Ibn Kathir Tafsir (7:180)", url: "https://quran.com/en/7:180/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "8:2",
      themeType: "Famous Ayah",
      shortTitle: "The Believers' Hearts Tremble at Allah's Mention",
      whyNotable: [
        "A defining ayah for the inner state of true believers.",
        "Frequently recited in reminders on iman and spiritual responsiveness.",
      ],
      summary:
        "Believers are described as those whose hearts respond with awe when Allah is remembered, and whose faith increases when revelation is recited. The ayah links iman to living responsiveness, not mere identity.",
      keyTakeaway: "Let remembrance and revelation actively increase your iman.",
      references: [
        { name: "Quran 8:2", url: "https://quran.com/8:2" },
        { name: "Ibn Kathir Tafsir (8:2)", url: "https://quran.com/en/8:2/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "8:24",
      themeType: "Famous Ayah",
      shortTitle: "Respond to What Gives You Life",
      whyNotable: [
        "A highly cited ayah on obedience as spiritual life.",
        "Widely used in calls to sincere response to Quran and Sunnah.",
      ],
      summary:
        "Believers are commanded to respond to Allah and His Messenger when called to what gives life. The ayah frames guidance as true vitality for the heart and community.",
      keyTakeaway: "Real life is in responding to revelation without delay.",
      references: [
        { name: "Quran 8:24", url: "https://quran.com/8:24" },
        { name: "Ibn Kathir Tafsir (8:24)", url: "https://quran.com/en/8:24/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  10: [
    {
      ayahRef: "8:60",
      themeType: "Famous Ayah",
      shortTitle: "Prepare Strength with Reliance on Allah",
      whyNotable: [
        "A very famous ayah on readiness and strategic responsibility.",
        "Frequently cited in discussions of disciplined preparation in deen.",
      ],
      summary:
        "Believers are commanded to prepare what strength they can for protection and deterrence. The ayah combines practical readiness with accountability to Allah.",
      keyTakeaway: "Preparation is an act of responsibility under Allah's command.",
      references: [
        { name: "Quran 8:60", url: "https://quran.com/8:60" },
        { name: "Ibn Kathir Tafsir (8:60)", url: "https://quran.com/en/8:60/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "8:63",
      themeType: "Famous Ayah",
      shortTitle: "Allah Unites Hearts",
      whyNotable: [
        "A major ayah on unity being a divine gift, not merely strategy.",
        "Commonly quoted in reminders on brotherhood and communal healing.",
      ],
      summary:
        "Allah states that He united believers' hearts, something wealth alone could never have accomplished. The ayah roots true unity in Allah's mercy and guidance.",
      keyTakeaway: "Seek unity through Allah's guidance, not worldly means alone.",
      references: [
        { name: "Quran 8:63", url: "https://quran.com/8:63" },
        { name: "Ibn Kathir Tafsir (8:63)", url: "https://quran.com/en/8:63/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "9:51",
      themeType: "Famous Ayah",
      shortTitle: "Nothing Befalls Us Except What Allah Decrees",
      whyNotable: [
        "One of the most quoted ayat for tawakkul in hardship.",
        "Widely recited for emotional steadiness and trust in qadr.",
      ],
      summary:
        "Believers are taught to say that nothing reaches them except what Allah has decreed. The ayah trains reliance, courage, and emotional balance through trust in Allah.",
      keyTakeaway: "Face uncertainty with tawakkul and confidence in Allah's decree.",
      references: [
        { name: "Quran 9:51", url: "https://quran.com/9:51" },
        { name: "Ibn Kathir Tafsir (9:51)", url: "https://quran.com/en/9:51/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "9:71",
      themeType: "Famous Ayah",
      shortTitle: "Believing Men and Women as Protecting Allies",
      whyNotable: [
        "A foundational ayah for shared duty in the believing community.",
        "Frequently cited for communal ethics and mutual responsibility.",
      ],
      summary:
        "The ayah describes believing men and women as allies who uphold good, restrain wrong, establish prayer, and obey Allah and His Messenger. It frames community strength through shared obedience.",
      keyTakeaway: "Build strong communities through mutual faith-driven responsibility.",
      references: [
        { name: "Quran 9:71", url: "https://quran.com/9:71" },
        { name: "Ibn Kathir Tafsir (9:71)", url: "https://quran.com/en/9:71/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "9:91",
      themeType: "Famous Ayah",
      shortTitle: "No Blame on the Weak if Sincere to Allah",
      whyNotable: [
        "A well-known ayah balancing legal duty with mercy and sincerity.",
        "Often cited to show Allah's justice and compassion in obligations.",
      ],
      summary:
        "This ayah lifts blame from those with genuine incapacity when they remain sincere to Allah and His Messenger. It affirms that Allah's law is rooted in justice, mercy, and truthful intention.",
      keyTakeaway: "Allah values sincerity and does not burden beyond genuine capacity.",
      references: [
        { name: "Quran 9:91", url: "https://quran.com/9:91" },
        { name: "Ibn Kathir Tafsir (9:91)", url: "https://quran.com/en/9:91/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
};

export const dayCorpusSummaries: Record<number, DayCorpusSummary> = {
  1: {
    title: "Day 1 Recitation Summary (Al-Baqarah 1-124)",
    summary:
      "Day 1 moves from faith foundations and Quranic proof to warnings against spiritual hardening, then closes with Ibrahim as a model of tested obedience and leadership.",
    themes: [
      "Guidance belongs to those who respond with taqwa and consistent worship.",
      "Ignoring clear revelation repeatedly can harden the heart.",
      "Leadership in deen follows obedience, sincerity, and justice.",
    ],
  },
  2: {
    title: "Day 2 Recitation Summary (Al-Baqarah 142-251)",
    summary:
      "Day 2 centers on communal identity, righteous character, Ramadan discipline, and reliance on Allah through powerful Quranic duas.",
    themes: [
      "Balanced Muslim identity is tied to justice and witness-bearing.",
      "Fasting is prescribed to cultivate taqwa and inner discipline.",
      "Famous Quranic duas anchor the believer through hardship and hope.",
    ],
  },
  3: {
    title: "Day 3 Recitation Summary (Al-Baqarah 253-286, Aal-i-Imraan 1-92)",
    summary:
      "Day 3 closes Al-Baqarah with major faith and dua passages, then opens Aal-i-Imraan with guidance on steadfast belief, sincerity, and sacrifice.",
    themes: [
      "Ayat al-Kursi and the closing ayat of Al-Baqarah reinforce tawhid, reliance, and repentance.",
      "Early Aal-i-Imraan repeatedly calls for firmness after guidance and truthful obedience.",
      "Real righteousness is measured by what we are willing to give for Allah's sake.",
    ],
  },
  4: {
    title: "Day 4 Recitation Summary (Aal-i-Imraan 92-200, An-Nisaa 1-23)",
    summary:
      "Day 4 emphasizes sincere sacrifice, unity upon revelation, steadfastness under pressure, and deep reliance on Allah through Quranic supplications. It closes with social accountability and family ethics in the opening of An-Nisaa.",
    themes: [
      "Steadfast faith is sustained by obedience, unity, and remembrance.",
      "Powerful Quranic duas train the heart for patience and trust in Allah.",
      "Taqwa extends from worship into family rights, justice, and social conduct.",
    ],
  },
  5: {
    title: "Day 5 Recitation Summary (An-Nisaa 24-147)",
    summary:
      "Day 5 covers a broad section of An-Nisaa, linking family and social law to justice, trust, and sincere obedience. The recitation moves from lawful boundaries and rights into communal responsibility, warnings against hypocrisy, and calls to hold firmly to revelation with integrity.",
    themes: [
      "Legal rulings in family, wealth, and social relations are tied to taqwa and accountability before Allah.",
      "Believers are called to justice, trustworthy conduct, and firm commitment to revelation in both private and public life.",
      "The passage repeatedly contrasts sincere iman with hypocrisy, urging repentance, clarity, and steadfast obedience.",
    ],
  },
  6: {
    title: "Day 6 Recitation Summary (An-Nisaa 147-176, Al-Maaida 1-81)",
    summary:
      "Day 6 moves from calls to gratitude, sincerity, and clarity of belief into major ethical foundations in Al-Maaida: covenant, justice, cooperation in righteousness, and steadfast moral responsibility.",
    themes: [
      "Faith is sustained through gratitude, truthfulness, and clear commitment to revelation.",
      "Justice and principled conduct are non-negotiable, even under tension or bias.",
      "Communal strength comes from cooperation in taqwa and refusing to normalize wrongdoing.",
    ],
  },
  7: {
    title: "Day 7 Recitation Summary (Al-Maaida 75-120, Al-An'aam 1-110)",
    summary:
      "Day 7 moves from clarifying belief and lawful boundaries in Al-Maaida to foundational tawhid themes in Al-An'aam. The recitation emphasizes devotion to Allah alone, disciplined obedience, and wisdom in public religious conduct.",
    themes: [
      "Belief is purified by rejecting shirk and turning fully to Allah in sincerity.",
      "Moral discipline includes leaving corrupting influences and guarding personal accountability.",
      "Quranic guidance calls for principled speech and wisdom that prevents greater harm.",
    ],
  },
  8: {
    title: "Day 8 Recitation Summary (Al-An'aam 111-165, Al-A'raaf 1-161)",
    summary:
      "Day 8 reinforces submission to clear guidance in Al-An'aam, then moves through major scenes of warning, repentance, and prophetic steadfastness in Al-A'raaf. The recitation repeatedly calls to humility before revelation, sincere tawbah, and moral discipline.",
    themes: [
      "Guidance is accepted through surrender, not selective obedience.",
      "The stories in Al-A'raaf warn against arrogance and delaying repentance.",
      "Steadfast faith combines tawhid, gratitude, and accountability to Allah.",
    ],
  },
  9: {
    title: "Day 9 Recitation Summary (Al-A'raaf 85-206, Al-Anfaal 1-40)",
    summary:
      "Day 9 closes Al-A'raaf with warnings against arrogance, calls to repentance, and devotion through Allah's beautiful names, then opens Al-Anfaal with foundations of iman, obedience, and disciplined communal responsibility.",
    themes: [
      "Late Al-A'raaf emphasizes humility, repentance, and truthful submission to revelation.",
      "Believers are shaped by responsive hearts, obedience, and trust in Allah's judgment.",
      "Early Al-Anfaal links spiritual life to disciplined response to Allah and His Messenger.",
    ],
  },
  10: {
    title: "Day 10 Recitation Summary (Al-Anfaal 41-75, At-Tawba 1-91)",
    summary:
      "Day 10 moves through obedience, readiness, and reliance in Al-Anfaal, then into major covenant and accountability themes in At-Tawba. The recitation stresses truthfulness, sincerity, and steadfast commitment under pressure.",
    themes: [
      "Preparation and communal discipline are part of faithful responsibility.",
      "Trust in Allah's decree strengthens believers through uncertainty and trial.",
      "At-Tawba repeatedly distinguishes sincere commitment from hypocrisy and excuse-making.",
    ],
  },
};

export function isTafsirReference(reference: HighlightReference): boolean {
  const text = `${reference.name} ${reference.url}`.toLowerCase();
  return (
    text.includes("tafsir") ||
    text.includes("ibn-kathir") ||
    text.includes("tabari") ||
    text.includes("qurtubi") ||
    text.includes("saadi") ||
    text.includes("jalalayn")
  );
}

export function isQuranTextReference(reference: HighlightReference): boolean {
  const text = `${reference.name} ${reference.url}`.toLowerCase();
  return text.includes("quran.com") || text.includes("qur'an") || text.includes("quran ");
}

export function getValidatedDayHighlights(day: number): DayHighlightItem[] {
  return (dayHighlights[day] || []).filter((item) => item.references.some(isTafsirReference));
}
