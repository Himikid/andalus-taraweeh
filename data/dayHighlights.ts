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
  11: [
    {
      ayahRef: "9:93",
      themeType: "Famous Ayah",
      shortTitle: "Sincerity Over Excuses",
      whyNotable: [
        "A clear ayah distinguishing sincere incapacity from empty excuses.",
        "Often cited to emphasize truthful accountability before Allah.",
      ],
      summary:
        "This ayah reproaches those who sought exemption despite being capable, exposing spiritual complacency and preference for ease over obedience.",
      keyTakeaway: "Do not normalize excuses when Allah has already granted capacity.",
      references: [
        { name: "Quran 9:93", url: "https://quran.com/9:93" },
        { name: "Ibn Kathir Tafsir (9:93)", url: "https://quran.com/en/9:93/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "10:26",
      themeType: "Famous Ayah",
      shortTitle: "Ihsan and More with Allah",
      whyNotable: [
        "A widely loved ayah promising reward and increase for excellence.",
        "Frequently quoted in reminders about ihsan and hope in Allah's mercy.",
      ],
      summary:
        "Allah promises those who excel in faith and worship the best reward and increase, with dignity and no humiliation on their faces.",
      keyTakeaway: "Pursue ihsan consistently; Allah's reward exceeds effort.",
      references: [
        { name: "Quran 10:26", url: "https://quran.com/10:26" },
        { name: "Ibn Kathir Tafsir (10:26)", url: "https://quran.com/en/10:26/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "10:109",
      themeType: "Famous Ayah",
      shortTitle: "Follow Revelation and Be Patient",
      whyNotable: [
        "A powerful closing command of Surah Yunus on perseverance.",
        "Commonly referenced for steadfastness when outcomes are delayed.",
      ],
      summary:
        "The Messenger is commanded to follow revelation and remain patient until Allah's judgment comes, affirming that He is the best of judges.",
      keyTakeaway: "Steadfastness means continuing revelation-led action with patience.",
      references: [
        { name: "Quran 10:109", url: "https://quran.com/10:109" },
        { name: "Ibn Kathir Tafsir (10:109)", url: "https://quran.com/en/10:109/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  13: [
    {
      ayahRef: "12:87",
      themeType: "Famous Ayah",
      shortTitle: "Do Not Despair of Allah's Mercy",
      whyNotable: [
        "A widely cited ayah for hope and refusing despair after prolonged hardship.",
        "Frequently referenced in reminders on tawakkul and emotional resilience.",
      ],
      summary:
        "Ya'qub commands his sons to seek out Yusuf and never despair of relief from Allah. The ayah teaches that hopelessness is not the way of believers.",
      keyTakeaway: "Hold onto hope in Allah even when tests are long and unresolved.",
      references: [
        { name: "Quran 12:87", url: "https://quran.com/12:87" },
        { name: "Ibn Kathir Tafsir (12:87)", url: "https://quran.com/en/12:87/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "12:101",
      themeType: "Dua",
      shortTitle: "Dua of Yusuf for a Righteous End",
      whyNotable: [
        "A famous Quranic dua combining gratitude, sincerity, and longing for a good ending.",
        "Frequently memorized and recited in personal supplication.",
      ],
      summary:
        "Yusuf acknowledges Allah's favors, asks for steadfast submission at death, and asks to be joined with the righteous. It is a model dua for humility after success.",
      keyTakeaway: "Seek a faithful ending and righteous company, not worldly status alone.",
      references: [
        { name: "Quran 12:101", url: "https://quran.com/12:101" },
        { name: "Ibn Kathir Tafsir (12:101)", url: "https://quran.com/en/12:101/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "13:11",
      themeType: "Famous Ayah",
      shortTitle: "Allah Changes People Who Change Themselves",
      whyNotable: [
        "One of the most quoted ayat on reform and accountability.",
        "Widely used in teaching personal and collective renewal.",
      ],
      summary:
        "The ayah states that Allah does not change the condition of a people until they change what is within themselves. It links transformation to inner repentance and sustained obedience.",
      keyTakeaway: "Lasting change begins with sincere inner reform before Allah.",
      references: [
        { name: "Quran 13:11", url: "https://quran.com/13:11" },
        { name: "Ibn Kathir Tafsir (13:11)", url: "https://quran.com/en/13:11/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "13:28",
      themeType: "Famous Ayah",
      shortTitle: "Hearts Find Rest in Allah's Remembrance",
      whyNotable: [
        "A central and beloved ayah on spiritual tranquility.",
        "Frequently quoted in khutbahs, dhikr reminders, and counseling contexts.",
      ],
      summary:
        "Allah describes true comfort as a state found in remembrance of Him. The ayah reframes inner peace as an outcome of dhikr and iman rather than external circumstances.",
      keyTakeaway: "Stability of heart comes from constant remembrance of Allah.",
      references: [
        { name: "Quran 13:28", url: "https://quran.com/13:28" },
        { name: "Ibn Kathir Tafsir (13:28)", url: "https://quran.com/en/13:28/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "14:7",
      themeType: "Famous Ayah",
      shortTitle: "Gratitude Brings Increase",
      whyNotable: [
        "A highly famous ayah used to teach shukr and warning against ingratitude.",
        "Commonly referenced in sermons and Islamic education.",
      ],
      summary:
        "Allah declares that gratitude leads to increase, while ingratitude invites severe consequence. The ayah anchors shukr as an active spiritual and ethical posture.",
      keyTakeaway: "Practice gratitude consistently to preserve and increase blessings.",
      references: [
        { name: "Quran 14:7", url: "https://quran.com/14:7" },
        { name: "Ibn Kathir Tafsir (14:7)", url: "https://quran.com/en/14:7/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "14:40-41",
      themeType: "Dua",
      shortTitle: "Dua of Ibrahim for Prayer and Forgiveness",
      whyNotable: [
        "A famous Quranic dua recited for family guidance and forgiveness.",
        "Widely memorized for asking steadfast prayer across generations.",
      ],
      summary:
        "Ibrahim asks Allah to make him and his descendants steadfast in prayer, and then asks forgiveness for himself, his parents, and the believers. The dua combines worship consistency with mercy and concern for others.",
      keyTakeaway: "Ask Allah for lasting prayer, family guidance, and broad forgiveness.",
      references: [
        { name: "Quran 14:40-41", url: "https://quran.com/14:40-41" },
        { name: "Ibn Kathir Tafsir (14:40)", url: "https://quran.com/en/14:40/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  14: [
    {
      ayahRef: "15:9",
      themeType: "Famous Ayah",
      shortTitle: "Allah Preserves the Reminder",
      whyNotable: [
        "A foundational ayah cited for divine preservation of the Quran.",
        "Frequently referenced in aqidah and Quran sciences teaching.",
      ],
      summary:
        "Allah declares that He revealed the Reminder and that He Himself will preserve it. The ayah anchors certainty in the Quran's protection across generations.",
      keyTakeaway: "Trust the Quran as divinely guarded guidance for all times.",
      references: [
        { name: "Quran 15:9", url: "https://quran.com/15:9" },
        { name: "Ibn Kathir Tafsir (15:9)", url: "https://quran.com/en/15:9/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "15:99",
      themeType: "Famous Ayah",
      shortTitle: "Worship Until Certainty",
      whyNotable: [
        "A famous closing command in Surah Al-Hijr on lifelong devotion.",
        "Widely cited in reminders on consistency and steadfast worship.",
      ],
      summary:
        "Allah commands the Prophet to continue worshiping his Lord until certainty comes. The ayah teaches constancy in worship through all phases of life.",
      keyTakeaway: "Remain consistent in worship without waiting for ideal conditions.",
      references: [
        { name: "Quran 15:99", url: "https://quran.com/15:99" },
        { name: "Ibn Kathir Tafsir (15:99)", url: "https://quran.com/en/15:99/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "16:90",
      themeType: "Famous Ayah",
      shortTitle: "Justice, Excellence, and Moral Restraint",
      whyNotable: [
        "One of the most famous ayat recited in khutbahs globally.",
        "A concise ethical framework covering justice, ihsan, and social conduct.",
      ],
      summary:
        "Allah commands justice, excellence, and generosity to relatives, and forbids indecency, wrongdoing, and transgression. The ayah gathers core social ethics in one powerful command.",
      keyTakeaway: "Live Islam through justice, ihsan, and disciplined restraint from harm.",
      references: [
        { name: "Quran 16:90", url: "https://quran.com/16:90" },
        { name: "Ibn Kathir Tafsir (16:90)", url: "https://quran.com/en/16:90/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "16:97",
      themeType: "Famous Ayah",
      shortTitle: "A Good Life Through Faith and Righteous Deeds",
      whyNotable: [
        "A highly cited ayah on dignified living through iman and righteous action.",
        "Often referenced to emphasize spiritual quality of life beyond material measure.",
      ],
      summary:
        "Allah promises believers who do righteous deeds, male or female, a good life and a better reward in the Hereafter. The ayah links inner well-being to faith-driven action.",
      keyTakeaway: "Real fulfillment is built on iman and righteous deeds, not appearances.",
      references: [
        { name: "Quran 16:97", url: "https://quran.com/16:97" },
        { name: "Ibn Kathir Tafsir (16:97)", url: "https://quran.com/en/16:97/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "16:125",
      themeType: "Famous Ayah",
      shortTitle: "Call to Allah with Wisdom",
      whyNotable: [
        "A central ayah for da'wah methodology and adab of dialogue.",
        "Frequently taught in outreach, education, and community leadership contexts.",
      ],
      summary:
        "Believers are commanded to invite to Allah's path with wisdom, good instruction, and the best manner of discussion. The ayah sets tone, method, and intention for principled da'wah.",
      keyTakeaway: "Effective da'wah requires wisdom, mercy, and disciplined speech.",
      references: [
        { name: "Quran 16:125", url: "https://quran.com/16:125" },
        { name: "Ibn Kathir Tafsir (16:125)", url: "https://quran.com/en/16:125/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "16:128",
      themeType: "Famous Ayah",
      shortTitle: "Allah Is with the God-Conscious and the Excellent",
      whyNotable: [
        "A beloved closing ayah of Surah An-Nahl emphasizing divine support.",
        "Frequently used in reminders for endurance, taqwa, and ihsan.",
      ],
      summary:
        "The surah closes by affirming Allah's special support for those who have taqwa and those who excel. It seals the passage with reassurance for believers striving under pressure.",
      keyTakeaway: "Pursue taqwa and ihsan to remain under Allah's aid.",
      references: [
        { name: "Quran 16:128", url: "https://quran.com/16:128" },
        { name: "Ibn Kathir Tafsir (16:128)", url: "https://quran.com/en/16:128/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  15: [
    {
      ayahRef: "17:1",
      themeType: "Famous Ayah",
      shortTitle: "The Night Journey Sign",
      whyNotable: [
        "A foundational ayah introducing Al-Israa and the sacred Night Journey.",
        "Frequently cited in discussions on Allah's power and the honor of the Prophet.",
      ],
      summary:
        "Allah opens the surah by declaring His transcendence and mentioning the Night Journey of His servant from Al-Masjid Al-Haram to Al-Masjid Al-Aqsa. The ayah anchors certainty in Allah's limitless power and signs.",
      keyTakeaway: "Approach revelation with awe and trust in Allah's absolute power.",
      references: [
        { name: "Quran 17:1", url: "https://quran.com/17:1" },
        { name: "Ibn Kathir Tafsir (17:1)", url: "https://quran.com/en/17:1/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "17:9",
      themeType: "Famous Ayah",
      shortTitle: "The Quran Guides to What Is Most Upright",
      whyNotable: [
        "A central ayah on the Quran's role as direct, upright guidance.",
        "Widely referenced in reminders on building life through revelation.",
      ],
      summary:
        "Allah states that this Quran guides to what is most upright and gives glad tidings to believers who do righteous deeds. It connects right direction to revelation-led living and action.",
      keyTakeaway: "Use the Quran as the primary compass for belief, character, and decisions.",
      references: [
        { name: "Quran 17:9", url: "https://quran.com/17:9" },
        { name: "Ibn Kathir Tafsir (17:9)", url: "https://quran.com/en/17:9/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "17:23-24",
      themeType: "Famous Ayah",
      shortTitle: "Excellence to Parents",
      whyNotable: [
        "Among the most cited ayat on birr al-walidayn and speech ethics.",
        "Often taught as a practical standard for mercy, humility, and gratitude.",
      ],
      summary:
        "Allah commands worship of Him alone and immediate excellence to parents, especially in old age, forbidding even minor harshness in speech. The passage teaches gentleness, dua, and humble service.",
      keyTakeaway: "Tawhid and honoring parents are inseparable acts of obedience.",
      references: [
        { name: "Quran 17:23-24", url: "https://quran.com/17:23-24" },
        { name: "Ibn Kathir Tafsir (17:23)", url: "https://quran.com/en/17:23/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "17:32",
      themeType: "Famous Ayah",
      shortTitle: "Do Not Go Near Zina",
      whyNotable: [
        "A key Quranic boundary that forbids paths leading to major sin.",
        "Frequently referenced in teaching prevention, modesty, and moral safeguards.",
      ],
      summary:
        "Allah commands believers not merely to avoid zina itself but to avoid approaching it. The ayah establishes proactive moral protection, not reactive regret.",
      keyTakeaway: "Guard your environment and habits before temptation escalates.",
      references: [
        { name: "Quran 17:32", url: "https://quran.com/17:32" },
        { name: "Ibn Kathir Tafsir (17:32)", url: "https://quran.com/en/17:32/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "17:70",
      themeType: "Famous Ayah",
      shortTitle: "The Dignity of the Children of Adam",
      whyNotable: [
        "A major ayah on human honor, stewardship, and accountability.",
        "Often cited in discussions on sacred human value and ethical conduct.",
      ],
      summary:
        "Allah affirms that He has honored the children of Adam and provided them with means of life on land and sea. The ayah frames human dignity as a divine trust tied to responsibility.",
      keyTakeaway: "Treat human life with dignity because honor is granted by Allah.",
      references: [
        { name: "Quran 17:70", url: "https://quran.com/17:70" },
        { name: "Ibn Kathir Tafsir (17:70)", url: "https://quran.com/en/17:70/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "17:111",
      themeType: "Famous Ayah",
      shortTitle: "Perfect Praise and Takbir for Allah",
      whyNotable: [
        "A powerful closing ayah affirming pure tawhid and divine perfection.",
        "Frequently used in reminders on praising Allah with proper creed.",
      ],
      summary:
        "The surah closes with praise of Allah, negating offspring, partnership, and weakness in His dominion, then commanding takbir. It seals Al-Israa with uncompromised tawhid and glorification.",
      keyTakeaway: "End every effort with pure praise and exaltation of Allah alone.",
      references: [
        { name: "Quran 17:111", url: "https://quran.com/17:111" },
        { name: "Ibn Kathir Tafsir (17:111)", url: "https://quran.com/en/17:111/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  16: [
    {
      ayahRef: "19:16",
      themeType: "Famous Ayah",
      shortTitle: "Maryam Withdraws for Devotion",
      whyNotable: [
        "A central opening scene of Surah Maryam showing sincere seclusion for worship.",
        "Frequently cited in reflections on purity, modesty, and spiritual focus.",
      ],
      summary:
        "Maryam is remembered as she withdrew from her people to an eastern place for devotion. The ayah opens the narrative with reverence, chastity, and intentional worship.",
      keyTakeaway: "Create sincere spaces of worship and guarded devotion to Allah.",
      references: [
        { name: "Quran 19:16", url: "https://quran.com/19:16" },
        { name: "Ibn Kathir Tafsir (19:16)", url: "https://quran.com/en/19:16/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "19:58",
      themeType: "Famous Ayah",
      shortTitle: "The Prophets Wept in Sujood",
      whyNotable: [
        "A beloved ayah describing prophetic humility when hearing Allah's signs.",
        "Often used to teach khushu, crying in worship, and reverence for revelation.",
      ],
      summary:
        "Allah describes the honored prophets who, when His verses were recited to them, fell in prostration and wept. The ayah presents deep receptivity as the mark of the righteous.",
      keyTakeaway: "Let Quran recitation soften the heart into humility and obedience.",
      references: [
        { name: "Quran 19:58", url: "https://quran.com/19:58" },
        { name: "Ibn Kathir Tafsir (19:58)", url: "https://quran.com/en/19:58/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "20:25-28",
      themeType: "Dua",
      shortTitle: "Dua of Musa for Clarity and Ease",
      whyNotable: [
        "One of the most memorized Quranic duas before study and teaching.",
        "A timeless supplication for confidence, clarity, and effective speech.",
      ],
      summary:
        "Musa asks Allah to expand his chest, ease his task, and loosen his tongue so people can understand him. The dua combines spiritual reliance with practical readiness for responsibility.",
      keyTakeaway: "Begin difficult duties by asking Allah for clarity, ease, and truthful speech.",
      references: [
        { name: "Quran 20:25-28", url: "https://quran.com/20:25-28" },
        { name: "Ibn Kathir Tafsir (20:25)", url: "https://quran.com/en/20:25/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "20:82",
      themeType: "Famous Ayah",
      shortTitle: "Vast Forgiveness for the One Who Returns",
      whyNotable: [
        "A major ayah of hope balancing repentance with steadfast faith and action.",
        "Frequently quoted in reminders on tawbah and returning to Allah.",
      ],
      summary:
        "Allah declares immense forgiveness for the one who repents, believes, does righteous deeds, and remains guided. The ayah links forgiveness to sincere return and continuity in obedience.",
      keyTakeaway: "Keep returning to Allah with repentance and steady righteous action.",
      references: [
        { name: "Quran 20:82", url: "https://quran.com/20:82" },
        { name: "Ibn Kathir Tafsir (20:82)", url: "https://quran.com/en/20:82/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "20:114",
      themeType: "Dua",
      shortTitle: "My Lord, Increase Me in Knowledge",
      whyNotable: [
        "A foundational Quranic supplication for sacred learning.",
        "Commonly cited as a core ethic of lifelong knowledge-seeking.",
      ],
      summary:
        "Allah teaches the Prophet to supplicate, 'My Lord, increase me in knowledge.' The ayah establishes humility and constant growth as the proper posture toward revelation.",
      keyTakeaway: "Seek beneficial knowledge continuously through dua and discipline.",
      references: [
        { name: "Quran 20:114", url: "https://quran.com/20:114" },
        { name: "Ibn Kathir Tafsir (20:114)", url: "https://quran.com/en/20:114/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "21:69",
      themeType: "Famous Ayah",
      shortTitle: "The Fire Made Cool for Ibrahim",
      whyNotable: [
        "A famous ayah of divine protection and miraculous relief for a prophet under trial.",
        "Widely referenced to affirm Allah's control over all causes and outcomes.",
      ],
      summary:
        "Allah commands the fire to become coolness and safety for Ibrahim. The ayah is a direct sign that Allah can reverse expected harm for those who rely on Him.",
      keyTakeaway: "Trust Allah's protection even when outward circumstances appear overwhelming.",
      references: [
        { name: "Quran 21:69", url: "https://quran.com/21:69" },
        { name: "Ibn Kathir Tafsir (21:69)", url: "https://quran.com/en/21:69/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  17: [
    {
      ayahRef: "21:87",
      themeType: "Dua",
      shortTitle: "Dua of Yunus in Distress",
      whyNotable: [
        "One of the most famous Quranic duas for repentance in hardship.",
        "Widely recited when seeking relief through tawhid and humility.",
      ],
      summary:
        "Yunus calls upon Allah in the darknesses, affirming Allah's oneness and admitting his own wrong. The ayah models urgent repentance with pure tawhid.",
      keyTakeaway: "In distress, return to Allah with sincere tawbah and clear tawhid.",
      references: [
        { name: "Quran 21:87", url: "https://quran.com/21:87" },
        { name: "Ibn Kathir Tafsir (21:87)", url: "https://quran.com/en/21:87/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "22:77",
      themeType: "Famous Ayah",
      shortTitle: "Bow, Prostrate, and Do Good",
      whyNotable: [
        "A concise command joining worship with righteous action.",
        "Frequently cited in reminders on embodied submission.",
      ],
      summary:
        "Believers are commanded to bow, prostrate, worship their Lord, and do good so they may succeed. The ayah links ritual devotion and ethical conduct.",
      keyTakeaway: "Let worship and good deeds move together in daily life.",
      references: [
        { name: "Quran 22:77", url: "https://quran.com/22:77" },
        { name: "Ibn Kathir Tafsir (22:77)", url: "https://quran.com/en/22:77/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "22:78",
      themeType: "Famous Ayah",
      shortTitle: "Strive for Allah as He Deserves",
      whyNotable: [
        "A major ayah on purposeful striving and Muslim identity.",
        "Often quoted in calls to perseverance and communal responsibility.",
      ],
      summary:
        "Allah commands striving for His cause with true striving and reminds the ummah of its chosen mission. The ayah frames religion as committed worship, sacrifice, and witness-bearing.",
      keyTakeaway: "Treat commitment to Allah as a full-life mission, not occasional effort.",
      references: [
        { name: "Quran 22:78", url: "https://quran.com/22:78" },
        { name: "Ibn Kathir Tafsir (22:78)", url: "https://quran.com/en/22:78/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "23:1-2",
      themeType: "Famous Ayah",
      shortTitle: "Successful Believers and Khushu",
      whyNotable: [
        "A foundational passage defining the traits of true success.",
        "Commonly taught as the opening program of Surah Al-Mu'minoon.",
      ],
      summary:
        "The surah opens by declaring believers successful, beginning with those who are humbly attentive in prayer. Success is presented as spiritual focus before external achievement.",
      keyTakeaway: "Protect khushu in salah as the root of lasting success.",
      references: [
        { name: "Quran 23:1-2", url: "https://quran.com/23:1-2" },
        { name: "Ibn Kathir Tafsir (23:1)", url: "https://quran.com/en/23:1/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "23:97-98",
      themeType: "Dua",
      shortTitle: "Seeking Refuge from Shayateen",
      whyNotable: [
        "A direct Quranic dua for protection from satanic whispers and influence.",
        "Often recited for spiritual safeguarding and inner discipline.",
      ],
      summary:
        "The Prophet is taught to seek refuge from the provocations of devils and from their presence. The passage trains believers to seek constant divine protection from unseen harm.",
      keyTakeaway: "Make isti'adhah a daily guard against subtle spiritual attacks.",
      references: [
        { name: "Quran 23:97-98", url: "https://quran.com/23:97-98" },
        { name: "Ibn Kathir Tafsir (23:97)", url: "https://quran.com/en/23:97/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "24:20",
      themeType: "Famous Ayah",
      shortTitle: "Allah's Favor and Mercy Preserve Us",
      whyNotable: [
        "A powerful closing reminder in this portion of An-Noor against moral collapse.",
        "Highlights that protection and reform are by Allah's compassion.",
      ],
      summary:
        "Allah reminds believers that without His favor and mercy they would be lost, and that He is Most Kind and Merciful. The ayah grounds communal purity in gratitude and dependence on Allah.",
      keyTakeaway: "Remain grateful and humble, knowing guidance is Allah's mercy.",
      references: [
        { name: "Quran 24:20", url: "https://quran.com/24:20" },
        { name: "Ibn Kathir Tafsir (24:20)", url: "https://quran.com/en/24:20/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  18: [
    {
      ayahRef: "24:36-38",
      themeType: "Famous Ayah",
      shortTitle: "Houses Raised for Allah's Remembrance",
      whyNotable: [
        "A famous masjid-centered passage linking remembrance to spiritual success.",
        "Frequently cited to show that true devotion is not distracted by worldly trade.",
      ],
      summary:
        "Allah praises houses where His name is exalted and remembered morning and evening by men not distracted by commerce from dhikr, prayer, and zakah. The passage defines worship-centered living with fear of accountability and hope in divine reward.",
      keyTakeaway: "Build life around remembrance and salah, not around distraction.",
      references: [
        { name: "Quran 24:36-38", url: "https://quran.com/24:36-38" },
        { name: "Ibn Kathir Tafsir (24:36)", url: "https://quran.com/en/24:36/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "24:55",
      themeType: "Famous Ayah",
      shortTitle: "Promise of Establishment for Believers",
      whyNotable: [
        "A widely cited ayah on Allah's promise of succession, stability, and security for sincere believers.",
        "Often referenced in lessons on collective obedience and public trust in Allah.",
      ],
      summary:
        "Allah promises those who believe and do righteous deeds that He will grant them succession, establish their religion, and replace fear with security so long as they worship Him alone. The ayah links communal strength to tawhid and obedience.",
      keyTakeaway: "Collective honor comes through sincere iman and righteous action.",
      references: [
        { name: "Quran 24:55", url: "https://quran.com/24:55" },
        { name: "Ibn Kathir Tafsir (24:55)", url: "https://quran.com/en/24:55/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "25:63",
      themeType: "Famous Ayah",
      shortTitle: "Servants of the Most Merciful",
      whyNotable: [
        "A signature ayah introducing the famous 'Ibad ar-Rahman' character sequence.",
        "Regularly used in tarbiyah to define humility and dignified conduct.",
      ],
      summary:
        "The servants of the Most Merciful are described as those who walk gently on earth and respond to ignorance with peace. The ayah opens a practical blueprint of spiritual character rooted in mercy and restraint.",
      keyTakeaway: "Answer provocation with humility and principled calm.",
      references: [
        { name: "Quran 25:63", url: "https://quran.com/25:63" },
        { name: "Ibn Kathir Tafsir (25:63)", url: "https://quran.com/en/25:63/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "25:74",
      themeType: "Dua",
      shortTitle: "Dua for Family and Leadership in Taqwa",
      whyNotable: [
        "One of the most memorized Quranic duas for righteous family life.",
        "Widely recited for pious offspring and upright communal leadership.",
      ],
      summary:
        "Believers ask Allah to grant from their spouses and offspring comfort to their eyes and to make them leaders for the people of taqwa. The dua combines private household righteousness with public spiritual responsibility.",
      keyTakeaway: "Ask Allah for homes that nurture taqwa and service to deen.",
      references: [
        { name: "Quran 25:74", url: "https://quran.com/25:74" },
        { name: "Ibn Kathir Tafsir (25:74)", url: "https://quran.com/en/25:74/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "26:83-85",
      themeType: "Dua",
      shortTitle: "Dua of Ibrahim for Wisdom and Legacy",
      whyNotable: [
        "A famous cluster of prophetic duas recited for righteous legacy.",
        "Highlights humility in asking for wisdom, truthfulness, and Paradise.",
      ],
      summary:
        "Ibrahim asks his Lord for sound judgment, to be joined with the righteous, and for an honorable mention among later generations, then asks to be among the inheritors of the Garden of Bliss. The passage models expansive, akhirah-centered ambition through dua.",
      keyTakeaway: "Seek wisdom, righteous company, and a legacy anchored in the Hereafter.",
      references: [
        { name: "Quran 26:83-85", url: "https://quran.com/26:83-85" },
        { name: "Ibn Kathir Tafsir (26:83)", url: "https://quran.com/en/26:83/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "26:88-89",
      themeType: "Famous Ayah",
      shortTitle: "Only the Sound Heart Will Benefit",
      whyNotable: [
        "One of the most famous Quranic reminders on the Day of Judgment.",
        "Frequently cited in purification-of-heart teachings.",
      ],
      summary:
        "On the Day when wealth and children will not benefit, only the one who comes to Allah with a sound heart will be saved. The ayah redirects priorities from outward assets to inward sincerity.",
      keyTakeaway: "Prioritize heart purification over temporary worldly status.",
      references: [
        { name: "Quran 26:88-89", url: "https://quran.com/26:88-89" },
        { name: "Ibn Kathir Tafsir (26:88)", url: "https://quran.com/en/26:88/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  19: [
    {
      ayahRef: "28:24",
      themeType: "Dua",
      shortTitle: "Musa's Dua in Need",
      whyNotable: [
        "One of the most famous Quranic duas for provision and relief.",
        "Widely recited when seeking halal sustenance and Allah's help.",
      ],
      summary:
        "After serving the two women, Musa turned to Allah and said he was in desperate need of whatever good Allah sends down. The ayah models humility, dependence, and hope in divine provision.",
      keyTakeaway: "In hardship, ask Allah directly with humility and need.",
      references: [
        { name: "Quran 28:24", url: "https://quran.com/28:24" },
        { name: "Ibn Kathir Tafsir (28:24)", url: "https://quran.com/en/28:24/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "28:56",
      themeType: "Famous Ayah",
      shortTitle: "Guidance Belongs to Allah",
      whyNotable: [
        "A highly cited ayah clarifying that hidayah is from Allah alone.",
        "Frequently referenced in dawah, parenting, and personal reliance lessons.",
      ],
      summary:
        "Allah tells the Prophet that he cannot guide whom he loves, but Allah guides whom He wills. The ayah balances effort in dawah with complete reliance on Allah for hearts.",
      keyTakeaway: "Do your duty sincerely, then trust Allah for guidance outcomes.",
      references: [
        { name: "Quran 28:56", url: "https://quran.com/28:56" },
        { name: "Ibn Kathir Tafsir (28:56)", url: "https://quran.com/en/28:56/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "28:83",
      themeType: "Famous Ayah",
      shortTitle: "The Hereafter for the Humble",
      whyNotable: [
        "A famous ayah on humility, avoiding corruption, and seeking akhirah.",
        "Often quoted to define success beyond status and power.",
      ],
      summary:
        "Allah says the home of the Hereafter is for those who do not seek arrogance or corruption on earth. The ayah redirects ambition toward humility, integrity, and taqwa.",
      keyTakeaway: "Pursue the Hereafter through humility and clean conduct.",
      references: [
        { name: "Quran 28:83", url: "https://quran.com/28:83" },
        { name: "Ibn Kathir Tafsir (28:83)", url: "https://quran.com/en/28:83/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "29:2",
      themeType: "Famous Ayah",
      shortTitle: "Faith Is Tested",
      whyNotable: [
        "A well-known ayah framing trials as part of sincere iman.",
        "Commonly cited in reminders on sabr and steadfastness.",
      ],
      summary:
        "Allah asks whether people think they will be left to say 'we believe' without being tested. The ayah establishes trials as a refining path for truthful faith.",
      keyTakeaway: "Expect tests, and meet them with patience and truthfulness.",
      references: [
        { name: "Quran 29:2", url: "https://quran.com/29:2" },
        { name: "Ibn Kathir Tafsir (29:2)", url: "https://quran.com/en/29:2/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "29:41",
      themeType: "Famous Ayah",
      shortTitle: "The Spider's Fragile House",
      whyNotable: [
        "One of the most recognizable parables in Surah Al-Ankaboot.",
        "Widely used to explain the fragility of reliance on other than Allah.",
      ],
      summary:
        "Those who take protectors besides Allah are likened to a spider taking a house, while the frailest of houses is the spider's house. The ayah teaches that false dependencies collapse under real pressure.",
      keyTakeaway: "Build trust on Allah, not fragile worldly supports.",
      references: [
        { name: "Quran 29:41", url: "https://quran.com/29:41" },
        { name: "Ibn Kathir Tafsir (29:41)", url: "https://quran.com/en/29:41/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "29:45",
      themeType: "Famous Ayah",
      shortTitle: "Salah Guards from Corruption",
      whyNotable: [
        "A foundational ayah connecting prayer to moral transformation.",
        "Frequently cited in tarbiyah on the purpose and effect of salah.",
      ],
      summary:
        "Allah commands recitation of revelation and establishment of prayer, then states that prayer restrains from indecency and wrongdoing. The ayah joins Quran recitation, salah, and ethical reform.",
      keyTakeaway: "Treat salah as daily protection against sin and drift.",
      references: [
        { name: "Quran 29:45", url: "https://quran.com/29:45" },
        { name: "Ibn Kathir Tafsir (29:45)", url: "https://quran.com/en/29:45/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  20: [
    {
      ayahRef: "30:17-18",
      themeType: "Famous Ayah",
      shortTitle: "Tasbih Across the Day",
      whyNotable: [
        "A famous ayah pair anchoring daily remembrance in morning and evening.",
        "Frequently cited in reminders on disciplined dhikr rhythms.",
      ],
      summary:
        "Allah calls to glorify Him in the evening and morning, and affirms that all praise in the heavens and earth belongs to Him. The ayat frame dhikr as a structured, daily orientation of the heart.",
      keyTakeaway: "Keep remembrance consistent through fixed daily moments.",
      references: [
        { name: "Quran 30:17-18", url: "https://quran.com/30:17-18" },
        { name: "Ibn Kathir Tafsir (30:17)", url: "https://quran.com/en/30:17/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "30:21",
      themeType: "Famous Ayah",
      shortTitle: "Tranquility in Marriage",
      whyNotable: [
        "One of the most well-known ayat recited in nikah talks and family reminders.",
        "Defines marriage through sakinah, mawaddah, and rahmah.",
      ],
      summary:
        "Allah describes spouses as a sign from Him: a place of tranquility, affection, and mercy. The ayah frames family life as an arena of worship and gratitude.",
      keyTakeaway: "Build homes on mercy, tenderness, and God-conscious responsibility.",
      references: [
        { name: "Quran 30:21", url: "https://quran.com/30:21" },
        { name: "Ibn Kathir Tafsir (30:21)", url: "https://quran.com/en/30:21/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "31:17",
      themeType: "Famous Ayah",
      shortTitle: "Luqman's Counsel: Salah, Duty, Patience",
      whyNotable: [
        "A highly cited tarbiyah ayah for youth formation and character.",
        "Combines worship, social ethics, and sabr in one concise command.",
      ],
      summary:
        "Luqman instructs his son to establish prayer, command good, forbid wrong, and be patient over hardship. The ayah outlines balanced spiritual and moral maturity.",
      keyTakeaway: "Anchor reform in salah, principled action, and patience.",
      references: [
        { name: "Quran 31:17", url: "https://quran.com/31:17" },
        { name: "Ibn Kathir Tafsir (31:17)", url: "https://quran.com/en/31:17/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "32:16-17",
      themeType: "Famous Ayah",
      shortTitle: "Night Prayer and Hidden Reward",
      whyNotable: [
        "A famous passage on qiyam and sincere private devotion.",
        "Regularly quoted in encouragement toward night worship.",
      ],
      summary:
        "Believers rise from their beds to call on Allah with fear and hope, and spend from what He has provided. Their reward is described as beyond what any soul can fully imagine.",
      keyTakeaway: "Private worship builds depth that public effort cannot replace.",
      references: [
        { name: "Quran 32:16-17", url: "https://quran.com/32:16-17" },
        { name: "Ibn Kathir Tafsir (32:16)", url: "https://quran.com/en/32:16/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "33:56",
      themeType: "Famous Ayah",
      shortTitle: "Sending Salawat upon the Prophet",
      whyNotable: [
        "One of the most famous and widely recited ayat in Muslim practice.",
        "Central textual basis for regular salawat upon the Prophet ﷺ.",
      ],
      summary:
        "Allah declares that He and His angels send blessings upon the Prophet and commands believers to do the same. The ayah ties love of the Messenger to ongoing worshipful remembrance.",
      keyTakeaway: "Keep your tongue active with salawat consistently.",
      references: [
        { name: "Quran 33:56", url: "https://quran.com/33:56" },
        { name: "Ibn Kathir Tafsir (33:56)", url: "https://quran.com/en/33:56/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "33:70-71",
      themeType: "Famous Ayah",
      shortTitle: "Speak with Straightness",
      whyNotable: [
        "A highly cited ayah pair about disciplined speech and taqwa.",
        "Frequently used in character-building and communication ethics.",
      ],
      summary:
        "Believers are commanded to fear Allah and speak with upright, truthful speech. Allah promises rectification of deeds and forgiveness as outcomes of this discipline.",
      keyTakeaway: "Guard speech and Allah will rectify wider parts of life.",
      references: [
        { name: "Quran 33:70-71", url: "https://quran.com/33:70-71" },
        { name: "Ibn Kathir Tafsir (33:70)", url: "https://quran.com/en/33:70/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  21: [
    {
      ayahRef: "35:15",
      themeType: "Famous Ayah",
      shortTitle: "Our Need, Allah's Self-Sufficiency",
      whyNotable: [
        "A widely cited ayah that summarizes ubudiyyah and dependence on Allah.",
        "Frequently used in reminders on humility and sincerity in worship.",
      ],
      summary:
        "Allah declares that all people are in need of Him, while He alone is free of need and worthy of all praise. The ayah grounds the believer's life in humility and reliance.",
      keyTakeaway: "Begin every effort with recognition of your need for Allah.",
      references: [
        { name: "Quran 35:15", url: "https://quran.com/35:15" },
        { name: "Ibn Kathir Tafsir (35:15)", url: "https://quran.com/en/35:15/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "36:58",
      themeType: "Famous Ayah",
      shortTitle: "Salam from a Merciful Lord",
      whyNotable: [
        "One of the most beloved ayat describing the honor of the people of Jannah.",
        "Commonly quoted to cultivate longing for Allah's mercy and acceptance.",
      ],
      summary:
        "The people of Paradise are greeted with peace from a Lord full of mercy. The ayah offers profound hope and frames ultimate success as nearness to Allah's mercy.",
      keyTakeaway: "Live for the day you are greeted by Allah's peace.",
      references: [
        { name: "Quran 36:58", url: "https://quran.com/36:58" },
        { name: "Ibn Kathir Tafsir (36:58)", url: "https://quran.com/en/36:58/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "36:82",
      themeType: "Famous Ayah",
      shortTitle: "Kun Fayakoon",
      whyNotable: [
        "A highly famous statement of Allah's absolute command and power.",
        "Frequently recited in lessons on qadr, trust, and certainty in Allah's decree.",
      ],
      summary:
        "Allah's command, when He wills a thing, is only to say 'Be,' and it is. The ayah restores certainty that no matter is difficult for Allah.",
      keyTakeaway: "Trust Allah's power over outcomes beyond your control.",
      references: [
        { name: "Quran 36:82", url: "https://quran.com/36:82" },
        { name: "Ibn Kathir Tafsir (36:82)", url: "https://quran.com/en/36:82/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "37:100",
      themeType: "Dua",
      shortTitle: "Dua for Righteous Offspring",
      whyNotable: [
        "A famous prophetic dua from Ibrahim, widely recited by parents and families.",
        "Represents hope, patience, and trust in Allah's timing.",
      ],
      summary:
        "Ibrahim asks his Lord to grant him righteous offspring, and Allah responds with glad tidings. The ayah models sincere dua joined with patience and certainty.",
      keyTakeaway: "Ask Allah for righteous legacy with patience and trust.",
      references: [
        { name: "Quran 37:100", url: "https://quran.com/37:100" },
        { name: "Ibn Kathir Tafsir (37:100)", url: "https://quran.com/en/37:100/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "38:35",
      themeType: "Dua",
      shortTitle: "Sulaiman's Dua for Forgiveness and Unique Provision",
      whyNotable: [
        "A famous prophetic dua uniting repentance with purposeful leadership.",
        "Frequently cited in lessons on asking Allah with humility and clarity.",
      ],
      summary:
        "Sulaiman asks Allah for forgiveness and a kingdom not granted to anyone after him. The ayah teaches beginning requests with repentance and seeking gifts for righteous purpose.",
      keyTakeaway: "Start with istighfar, then ask Allah boldly for good.",
      references: [
        { name: "Quran 38:35", url: "https://quran.com/38:35" },
        { name: "Ibn Kathir Tafsir (38:35)", url: "https://quran.com/en/38:35/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "39:23",
      themeType: "Famous Ayah",
      shortTitle: "The Best Speech and the Responsive Heart",
      whyNotable: [
        "A major ayah describing the effect of the Quran on hearts and bodies.",
        "Widely quoted in reminders about deep, living engagement with revelation.",
      ],
      summary:
        "Allah describes the Quran as the best speech, repeated and consistent, causing the skins of those who fear Him to tremble, then soften into remembrance. The ayah defines true receptivity to revelation.",
      keyTakeaway: "Recite Quran to be transformed, not just informed.",
      references: [
        { name: "Quran 39:23", url: "https://quran.com/39:23" },
        { name: "Ibn Kathir Tafsir (39:23)", url: "https://quran.com/en/39:23/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  22: [
    {
      ayahRef: "40:44",
      themeType: "Dua",
      shortTitle: "I Entrust My Affair to Allah",
      whyNotable: [
        "A famous Quranic declaration of tawakkul repeated in personal hardship.",
        "Widely cited for calm reliance when truth is opposed.",
      ],
      summary:
        "The believing man from Pharaoh's family concludes by entrusting his entire affair to Allah, affirming that Allah sees all servants. The ayah captures principled speech followed by full reliance on divine judgment.",
      keyTakeaway: "After speaking truth, place outcomes fully with Allah.",
      references: [
        { name: "Quran 40:44", url: "https://quran.com/40:44" },
        { name: "Ibn Kathir Tafsir (40:44)", url: "https://quran.com/en/40:44/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "40:60",
      themeType: "Dua",
      shortTitle: "Call Upon Me, I Will Respond",
      whyNotable: [
        "One of the most quoted ayat on dua and divine response.",
        "Frequently recited to revive consistency in supplication.",
      ],
      summary:
        "Allah commands His servants to call upon Him and promises response, while warning against arrogant refusal to worship. The ayah directly links dua to servitude and humility before Allah.",
      keyTakeaway: "Treat dua as worship and return to it consistently.",
      references: [
        { name: "Quran 40:60", url: "https://quran.com/40:60" },
        { name: "Ibn Kathir Tafsir (40:60)", url: "https://quran.com/en/40:60/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "40:65",
      themeType: "Dua",
      shortTitle: "Call on Him with Pure Sincerity",
      whyNotable: [
        "A major ayah grounding dua in ikhlas and pure tawhid.",
        "Regularly cited in reminders on sincerity in worship.",
      ],
      summary:
        "Allah, the Ever-Living with no deity besides Him, commands believers to call on Him with religion made purely for Him. The ayah ties accepted worship to sincerity and undivided devotion.",
      keyTakeaway: "Purify intention before and during every dua.",
      references: [
        { name: "Quran 40:65", url: "https://quran.com/40:65" },
        { name: "Ibn Kathir Tafsir (40:65)", url: "https://quran.com/en/40:65/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "41:30",
      themeType: "Famous Ayah",
      shortTitle: "Steadfastness and Angelic Reassurance",
      whyNotable: [
        "A beloved ayah about istiqamah and divine reassurance at death and beyond.",
        "Widely referenced in reminders on courage and consistency.",
      ],
      summary:
        "Those who declare 'Our Lord is Allah' and remain steadfast are met by angels with reassurance not to fear or grieve, and glad tidings of Paradise. The ayah presents istiqamah as lived loyalty rewarded with divine comfort.",
      keyTakeaway: "Stay firm on Allah through consistency, not bursts.",
      references: [
        { name: "Quran 41:30", url: "https://quran.com/41:30" },
        { name: "Ibn Kathir Tafsir (41:30)", url: "https://quran.com/en/41:30/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "42:11",
      themeType: "Famous Ayah",
      shortTitle: "Nothing Is Like Him",
      whyNotable: [
        "A foundational aqidah ayah used to affirm Allah's absolute uniqueness.",
        "Central in mainstream Sunni teaching on names and attributes.",
      ],
      summary:
        "Allah affirms that nothing is comparable to Him while He is the All-Hearing, All-Seeing. The ayah balances transcendence and affirmed attributes without anthropomorphism.",
      keyTakeaway: "Affirm Allah as He described Himself, without distortion.",
      references: [
        { name: "Quran 42:11", url: "https://quran.com/42:11" },
        { name: "Ibn Kathir Tafsir (42:11)", url: "https://quran.com/en/42:11/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "42:38",
      themeType: "Famous Ayah",
      shortTitle: "Consultation as a Believer's Trait",
      whyNotable: [
        "A key ayah establishing shura as a standing community principle.",
        "Frequently cited in governance, leadership, and family decision ethics.",
      ],
      summary:
        "Believers are described as those who respond to their Lord, establish prayer, conduct their affairs by mutual consultation, and spend from what Allah provided. The ayah links spirituality with responsible, consultative social conduct.",
      keyTakeaway: "Build decisions around worship, shura, and accountability.",
      references: [
        { name: "Quran 42:38", url: "https://quran.com/42:38" },
        { name: "Ibn Kathir Tafsir (42:38)", url: "https://quran.com/en/42:38/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  23: [
    {
      ayahRef: "44:3-4",
      themeType: "Famous Ayah",
      shortTitle: "A Blessed Night of Revelation",
      whyNotable: [
        "A famous passage linked to the blessed descent of Quranic guidance.",
        "Frequently cited to emphasize revelation as mercy and warning.",
      ],
      summary:
        "Allah states that He sent the revelation down in a blessed night and that every wise matter is distinguished therein. The ayat frame revelation as deliberate divine mercy and guidance for accountability.",
      keyTakeaway: "Treat the Quran as a living mercy that directs every major decision.",
      references: [
        { name: "Quran 44:3-4", url: "https://quran.com/44:3-4" },
        { name: "Ibn Kathir Tafsir (44:3)", url: "https://quran.com/en/44:3/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "45:36-37",
      themeType: "Famous Ayah",
      shortTitle: "All Praise and Greatness Belong to Allah",
      whyNotable: [
        "A well-known closing declaration of praise and divine majesty.",
        "Used in reminders on humility before Allah's sovereignty.",
      ],
      summary:
        "These ayat conclude with total praise for Allah, Lord of the heavens and earth, and affirm His greatness and authority over all realms. They train the believer to end reflection in glorification and surrender.",
      keyTakeaway: "Close your reflection with hamd and recognition of Allah's absolute authority.",
      references: [
        { name: "Quran 45:36-37", url: "https://quran.com/45:36-37" },
        { name: "Ibn Kathir Tafsir (45:36)", url: "https://quran.com/en/45:36/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "46:15",
      themeType: "Dua",
      shortTitle: "Dua of Gratitude and Righteous Legacy",
      whyNotable: [
        "A highly recited Quranic dua for gratitude, righteous deeds, and righteous offspring.",
        "Commonly used in family and tarbiyah reminders.",
      ],
      summary:
        "The believer asks Allah to inspire gratitude for divine favors, to enable righteous action pleasing to Him, and to rectify one's offspring. The ayah combines personal reform, family concern, and repentance in one comprehensive supplication.",
      keyTakeaway: "Make gratitude and family righteousness part of your daily dua.",
      references: [
        { name: "Quran 46:15", url: "https://quran.com/46:15" },
        { name: "Ibn Kathir Tafsir (46:15)", url: "https://quran.com/en/46:15/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "47:7",
      themeType: "Famous Ayah",
      shortTitle: "Support Allah's Cause, Receive His Support",
      whyNotable: [
        "A famous principle ayah on divine aid and steadfastness.",
        "Widely cited in calls to sincere effort and perseverance.",
      ],
      summary:
        "Allah promises that those who support His cause will be supported by Him and have their steps made firm. The ayah anchors resilience in faithful commitment rather than worldly calculation.",
      keyTakeaway: "Stand for Allah sincerely and rely on His stabilizing support.",
      references: [
        { name: "Quran 47:7", url: "https://quran.com/47:7" },
        { name: "Ibn Kathir Tafsir (47:7)", url: "https://quran.com/en/47:7/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "48:4",
      themeType: "Famous Ayah",
      shortTitle: "Sakina Sent into Believing Hearts",
      whyNotable: [
        "A beloved ayah on divine tranquility in moments of strain.",
        "Frequently cited to explain calm conviction during trials.",
      ],
      summary:
        "Allah states that He sent tranquility into the hearts of believers so they would increase in faith upon faith. The ayah shows that inner steadiness is a divine gift that strengthens obedience and trust.",
      keyTakeaway: "Ask Allah for sakina when pressure rises and decisions feel heavy.",
      references: [
        { name: "Quran 48:4", url: "https://quran.com/48:4" },
        { name: "Ibn Kathir Tafsir (48:4)", url: "https://quran.com/en/48:4/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "48:29",
      themeType: "Famous Ayah",
      shortTitle: "Mercy Among Believers",
      whyNotable: [
        "A central and frequently quoted portrait of the Prophet and his companions.",
        "Used widely to define strength with principle and mercy within the believing community.",
      ],
      summary:
        "This ayah describes the Messenger of Allah and his companions as firm against rejection yet deeply merciful among themselves, marked by worship and sincere devotion. It presents communal strength as worship-rooted character, not harshness.",
      keyTakeaway: "Build communities that combine principled firmness with mercy and worship.",
      references: [
        { name: "Quran 48:29", url: "https://quran.com/48:29" },
        { name: "Ibn Kathir Tafsir (48:29)", url: "https://quran.com/en/48:29/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  24: [
    {
      ayahRef: "49:13",
      themeType: "Famous Ayah",
      shortTitle: "Honor Is Through Taqwa",
      whyNotable: [
        "A universally cited ayah on equality, dignity, and taqwa-based honor.",
        "Frequently referenced in khutbahs on unity and anti-racism.",
      ],
      summary:
        "Allah reminds humanity that people were created from male and female and made into peoples and tribes to know one another, not to claim superiority. The ayah sets taqwa as the only true criterion of honor before Allah.",
      keyTakeaway: "Measure status by taqwa and character, not background.",
      references: [
        { name: "Quran 49:13", url: "https://quran.com/49:13" },
        { name: "Ibn Kathir Tafsir (49:13)", url: "https://quran.com/en/49:13/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "50:16",
      themeType: "Famous Ayah",
      shortTitle: "Allah Is Nearer Than the Jugular",
      whyNotable: [
        "A highly famous ayah used in reminders on muraqabah and inner accountability.",
        "Widely cited to cultivate conscious awareness of Allah.",
      ],
      summary:
        "Allah declares that He created the human being, knows what the self whispers, and is nearer than the jugular vein. The ayah anchors vigilance, sincerity, and immediate accountability before Allah.",
      keyTakeaway: "Live with constant awareness that Allah knows the inner state.",
      references: [
        { name: "Quran 50:16", url: "https://quran.com/50:16" },
        { name: "Ibn Kathir Tafsir (50:16)", url: "https://quran.com/en/50:16/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "51:56",
      themeType: "Famous Ayah",
      shortTitle: "Created to Worship",
      whyNotable: [
        "One of the most foundational ayat on life's purpose in Islam.",
        "Central to teaching worship, servitude, and intentional living.",
      ],
      summary:
        "Allah states that jinn and humankind were created only to worship Him. The ayah provides the core lens through which all goals, work, and relationships are measured.",
      keyTakeaway: "Let every part of life orbit sincere worship of Allah.",
      references: [
        { name: "Quran 51:56", url: "https://quran.com/51:56" },
        { name: "Ibn Kathir Tafsir (51:56)", url: "https://quran.com/en/51:56/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "54:17",
      themeType: "Famous Ayah",
      shortTitle: "The Quran Made Easy for Reminder",
      whyNotable: [
        "A repeated refrain in Surah Al-Qamar that is widely memorized and quoted.",
        "Often used to encourage direct engagement with Quran despite hesitation.",
      ],
      summary:
        "Allah repeatedly says that He has made the Quran easy for remembrance and asks whether there is anyone who will take heed. The ayah removes excuses and invites consistent, reflective return to revelation.",
      keyTakeaway: "Approach Quran regularly; Allah has opened its path for remembrance.",
      references: [
        { name: "Quran 54:17", url: "https://quran.com/54:17" },
        { name: "Ibn Kathir Tafsir (54:17)", url: "https://quran.com/en/54:17/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "55:13",
      themeType: "Famous Ayah",
      shortTitle: "Which of Your Lord's Favors Will You Deny?",
      whyNotable: [
        "The most recognizable refrain of Surah Ar-Rahman, repeated throughout the surah.",
        "Commonly recited to cultivate gratitude and awe.",
      ],
      summary:
        "This refrain repeatedly confronts both humans and jinn with Allah's countless favors and signs. Its repetition trains the heart to move from heedlessness to gratitude and humility.",
      keyTakeaway: "Count Allah's favors and answer them with gratitude and obedience.",
      references: [
        { name: "Quran 55:13", url: "https://quran.com/55:13" },
        { name: "Ibn Kathir Tafsir (55:13)", url: "https://quran.com/en/55:13/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "57:20",
      themeType: "Famous Ayah",
      shortTitle: "The World Is Temporary, the Hereafter Is Lasting",
      whyNotable: [
        "A highly cited ayah on the fleeting nature of dunya and the permanence of akhirah.",
        "Frequently used in reminders on priorities and detachment.",
      ],
      summary:
        "Allah describes worldly life as play, distraction, adornment, boasting, and rivalry, then contrasts it with lasting outcome in the Hereafter. The ayah recalibrates ambition toward what remains with Allah.",
      keyTakeaway: "Use dunya as a path to akhirah, not as a final destination.",
      references: [
        { name: "Quran 57:20", url: "https://quran.com/57:20" },
        { name: "Ibn Kathir Tafsir (57:20)", url: "https://quran.com/en/57:20/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  25: [
    {
      ayahRef: "58:11",
      themeType: "Famous Ayah",
      shortTitle: "Allah Raises People of Knowledge and Iman",
      whyNotable: [
        "A highly cited ayah on adab, humility, and the rank granted by Allah.",
        "Frequently quoted in learning circles to connect ilm with faith and obedience.",
      ],
      summary:
        "Allah commands believers to make space in gatherings and to rise when instructed, then promises elevation for those who believe and those given knowledge. The ayah links community adab to spiritual rank and divine awareness of all actions.",
      keyTakeaway: "Carry humility and discipline in gatherings so knowledge benefits the heart.",
      references: [
        { name: "Quran 58:11", url: "https://quran.com/58:11" },
        { name: "Ibn Kathir Tafsir (58:11)", url: "https://quran.com/en/58:11/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "59:10",
      themeType: "Dua",
      shortTitle: "Dua for Forgiveness and Clean Hearts",
      whyNotable: [
        "A famous Quranic dua for unity and purification from resentment.",
        "Widely used to mend relationships and preserve brotherhood among believers.",
      ],
      summary:
        "Believers ask Allah to forgive them and those who preceded them in faith, and to remove rancor from their hearts toward believers. The supplication combines humility, mercy for earlier generations, and inner purification.",
      keyTakeaway: "Protect unity by making dua for others and cleansing the heart of grudges.",
      references: [
        { name: "Quran 59:10", url: "https://quran.com/59:10" },
        { name: "Ibn Kathir Tafsir (59:10)", url: "https://quran.com/en/59:10/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "59:18",
      themeType: "Famous Ayah",
      shortTitle: "Prepare for Tomorrow",
      whyNotable: [
        "A central accountability ayah often quoted in reminders on self-audit.",
        "Commonly used to frame daily muhasabah before Allah.",
      ],
      summary:
        "Allah commands believers to have taqwa and to look at what each soul has sent forward for tomorrow. The ayah turns faith into proactive accountability, urging constant moral inventory.",
      keyTakeaway: "Review your actions regularly and invest intentionally for the Hereafter.",
      references: [
        { name: "Quran 59:18", url: "https://quran.com/59:18" },
        { name: "Ibn Kathir Tafsir (59:18)", url: "https://quran.com/en/59:18/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "59:22-24",
      themeType: "Famous Ayah",
      shortTitle: "The Beautiful Names of Allah",
      whyNotable: [
        "Among the most recited passages listing Allah's names and attributes.",
        "Used frequently in dhikr-focused reminders to deepen awe and ma'rifah.",
      ],
      summary:
        "These closing ayat of Al-Hashr present Allah's majestic names and attributes, affirming His perfection, sovereignty, and holiness. The passage trains hearts to know Allah through His names and worship Him with reverence.",
      keyTakeaway: "Strengthen worship by learning Allah's names and living by their meanings.",
      references: [
        { name: "Quran 59:22-24", url: "https://quran.com/59:22-24" },
        { name: "Ibn Kathir Tafsir (59:22)", url: "https://quran.com/en/59:22/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "62:9",
      themeType: "Famous Ayah",
      shortTitle: "Respond to the Call of Jumuah",
      whyNotable: [
        "The primary ayah on Jumuah obligation and prioritizing remembrance over trade.",
        "Frequently referenced in khutbahs about weekly spiritual discipline.",
      ],
      summary:
        "When the call for Friday prayer is made, believers are commanded to hasten to Allah's remembrance and leave trade. The ayah prioritizes worship and collective dhikr over immediate worldly gain.",
      keyTakeaway: "Treat Jumuah as a non-negotiable weekly covenant with Allah.",
      references: [
        { name: "Quran 62:9", url: "https://quran.com/62:9" },
        { name: "Ibn Kathir Tafsir (62:9)", url: "https://quran.com/en/62:9/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "63:9",
      themeType: "Famous Ayah",
      shortTitle: "Do Not Let Wealth Distract from Dhikr",
      whyNotable: [
        "A well-known warning ayah on wealth and family distractions.",
        "Commonly cited to recalibrate priorities around remembrance and obedience.",
      ],
      summary:
        "Believers are warned not to let wealth and children distract them from the remembrance of Allah, because that neglect is true loss. The ayah reframes success around dhikr-centered living.",
      keyTakeaway: "Keep remembrance of Allah central so worldly blessings do not become trials.",
      references: [
        { name: "Quran 63:9", url: "https://quran.com/63:9" },
        { name: "Ibn Kathir Tafsir (63:9)", url: "https://quran.com/en/63:9/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  26: [
    {
      ayahRef: "64:16",
      themeType: "Famous Ayah",
      shortTitle: "Fear Allah as Much as You Are Able",
      whyNotable: [
        "A foundational ayah for practical taqwa, obedience, and sincere striving.",
        "Frequently cited in teaching balance between duty, capacity, and consistency.",
      ],
      summary:
        "Allah commands believers to be mindful of Him to the extent of their ability, to listen and obey, and to spend for their own ultimate good. The ayah ties taqwa to actionable discipline and warns against inner greed.",
      keyTakeaway: "Make steady obedience your standard, even when full perfection is difficult.",
      references: [
        { name: "Quran 64:16", url: "https://quran.com/64:16" },
        { name: "Ibn Kathir Tafsir (64:16)", url: "https://quran.com/en/64:16/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "65:2-3",
      themeType: "Famous Ayah",
      shortTitle: "Whoever Has Taqwa, Allah Makes a Way Out",
      whyNotable: [
        "Among the most cited ayat on relief, provision, and tawakkul.",
        "A central comfort passage recited in hardship reminders and counsel.",
      ],
      summary:
        "These ayat promise that whoever has taqwa, Allah grants a way out and provides from where one does not expect. They also anchor trust in Allah by affirming His sufficiency for those who rely on Him.",
      keyTakeaway: "Respond to pressure with taqwa and tawakkul, not panic.",
      references: [
        { name: "Quran 65:2-3", url: "https://quran.com/65:2-3" },
        { name: "Ibn Kathir Tafsir (65:2)", url: "https://quran.com/en/65:2/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "66:8",
      themeType: "Dua",
      shortTitle: "Our Lord, Perfect Our Light and Forgive Us",
      whyNotable: [
        "A renowned Quranic dua of tawbah, forgiveness, and hope on the Day of Judgment.",
        "Frequently used in Ramadan and nightly supplication gatherings.",
      ],
      summary:
        "Believers are taught to turn in sincere repentance and to ask Allah to perfect their light and forgive them. The dua combines accountability, hope, and dependence on Allah's absolute power.",
      keyTakeaway: "Make sincere repentance and this dua a regular part of worship.",
      references: [
        { name: "Quran 66:8", url: "https://quran.com/66:8" },
        { name: "Ibn Kathir Tafsir (66:8)", url: "https://quran.com/en/66:8/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "67:2",
      themeType: "Famous Ayah",
      shortTitle: "Life and Death as a Test",
      whyNotable: [
        "A famous purpose-defining ayah from Surah Al-Mulk recited widely at night.",
        "Regularly cited to frame life around ihsan and accountability.",
      ],
      summary:
        "Allah created death and life to test who is best in deeds, while He remains the Mighty and Forgiving. The ayah reframes life as an exam of excellence, not mere duration or appearance.",
      keyTakeaway: "Prioritize quality of deeds and sincerity over outward scale.",
      references: [
        { name: "Quran 67:2", url: "https://quran.com/67:2" },
        { name: "Ibn Kathir Tafsir (67:2)", url: "https://quran.com/en/67:2/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "67:15",
      themeType: "Famous Ayah",
      shortTitle: "Walk the Earth and Seek Provision",
      whyNotable: [
        "A widely referenced ayah balancing effort in dunya with certainty of return to Allah.",
        "Often used to teach halal striving with spiritual awareness.",
      ],
      summary:
        "Allah made the earth manageable, commanding people to travel its paths and eat from His provision, while reminding that final return is to Him. The ayah joins work, gratitude, and accountability in one ethic.",
      keyTakeaway: "Pursue livelihood actively while keeping akhirah central.",
      references: [
        { name: "Quran 67:15", url: "https://quran.com/67:15" },
        { name: "Ibn Kathir Tafsir (67:15)", url: "https://quran.com/en/67:15/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "69:52",
      themeType: "Famous Ayah",
      shortTitle: "Glorify the Name of Your Lord, the Most Great",
      whyNotable: [
        "A memorable closing command of Surah Al-Haqqah centered on tasbih.",
        "Used to seal reflection in reverence and exaltation of Allah.",
      ],
      summary:
        "After intense scenes of truth and final judgment, the surah closes with a direct command to glorify the name of the Most Great Lord. It channels awe into worship and immediate remembrance.",
      keyTakeaway: "Conclude reflection with tasbih and submission to Allah's greatness.",
      references: [
        { name: "Quran 69:52", url: "https://quran.com/69:52" },
        { name: "Ibn Kathir Tafsir (69:52)", url: "https://quran.com/en/69:52/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
  ],
  27: [
    {
      ayahRef: "71:10-12",
      themeType: "Dua",
      shortTitle: "Seek Forgiveness for Expansive Provision",
      whyNotable: [
        "A famous Quranic call linking istighfar with mercy, rain, wealth, and children.",
        "Widely recited in reminders on repentance and opening closed doors.",
      ],
      summary:
        "Nuh calls his people to seek Allah's forgiveness, promising that Allah is ever-forgiving and will send rain, wealth, and offspring as aid. The passage teaches that repentance is both spiritual purification and a means for worldly barakah.",
      keyTakeaway: "Make sincere istighfar constant, especially in hardship and stagnation.",
      references: [
        { name: "Quran 71:10-12", url: "https://quran.com/71:10-12" },
        { name: "Ibn Kathir Tafsir (71:10)", url: "https://quran.com/en/71:10/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "73:20",
      themeType: "Famous Ayah",
      shortTitle: "Recite What Is Easy from the Quran",
      whyNotable: [
        "A central ayah of practical worship balance in Surah Al-Muzzammil.",
        "Often cited to encourage consistent Quran recitation with realistic discipline.",
      ],
      summary:
        "Allah acknowledges varied human burdens and commands believers to recite what is manageable of the Quran, while upholding prayer, charity, and sincere striving. It frames consistency over unsustainable intensity.",
      keyTakeaway: "Build worship routines you can sustain with sincerity.",
      references: [
        { name: "Quran 73:20", url: "https://quran.com/73:20" },
        { name: "Ibn Kathir Tafsir (73:20)", url: "https://quran.com/en/73:20/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "74:38",
      themeType: "Famous Ayah",
      shortTitle: "Every Soul Is Held by What It Earned",
      whyNotable: [
        "A widely quoted accountability ayah from Surah Al-Muddaththir.",
        "Used frequently in reminders on personal responsibility before Allah.",
      ],
      summary:
        "This ayah states that every soul is pledged to what it has earned, anchoring moral responsibility without excuse-shifting. It sharpens the believer's focus on deeds, repentance, and preparation for judgment.",
      keyTakeaway: "Own your deeds now before they testify later.",
      references: [
        { name: "Quran 74:38", url: "https://quran.com/74:38" },
        { name: "Ibn Kathir Tafsir (74:38)", url: "https://quran.com/en/74:38/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "75:2",
      themeType: "Famous Ayah",
      shortTitle: "By the Self-Reproaching Soul",
      whyNotable: [
        "A profound ayah on conscience and inner moral awakening.",
        "Frequently cited in purification talks about muhasabah and repentance.",
      ],
      summary:
        "Allah swears by the self-reproaching soul, highlighting the inner faculty that recognizes fault and calls for correction. The ayah validates healthy remorse as a path back to Allah.",
      keyTakeaway: "Use conscience as a guide to repentance, not a trigger for despair.",
      references: [
        { name: "Quran 75:2", url: "https://quran.com/75:2" },
        { name: "Ibn Kathir Tafsir (75:2)", url: "https://quran.com/en/75:2/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "79:40-41",
      themeType: "Famous Ayah",
      shortTitle: "Restrain the Self, Earn Paradise",
      whyNotable: [
        "A famous passage on controlling desires and fearing standing before Allah.",
        "Commonly used in tarbiyah reminders on discipline and akhirah focus.",
      ],
      summary:
        "For the one who fears standing before Allah and restrains the self from unchecked desire, Paradise is promised as refuge. The ayah ties salvation to reverent fear and practical self-control.",
      keyTakeaway: "Real strength is saying no to desires that pull you from Allah.",
      references: [
        { name: "Quran 79:40-41", url: "https://quran.com/79:40-41" },
        { name: "Ibn Kathir Tafsir (79:40)", url: "https://quran.com/en/79:40/tafsirs/ar-tafsir-ibn-kathir" },
      ],
    },
    {
      ayahRef: "80:34-37",
      themeType: "Famous Ayah",
      shortTitle: "The Day Each Person Flees Even Loved Ones",
      whyNotable: [
        "A striking and frequently quoted akhirah scene from Surah Abasa.",
        "Used to awaken urgency and sincerity before the Day of Judgment.",
      ],
      summary:
        "These ayat describe a day when every person flees even closest family due to overwhelming personal concern. The scene strips false security and redirects the heart to sincere preparation.",
      keyTakeaway: "Prepare now for the Day when only your deeds remain with you.",
      references: [
        { name: "Quran 80:34-37", url: "https://quran.com/80:34-37" },
        { name: "Ibn Kathir Tafsir (80:34)", url: "https://quran.com/en/80:34/tafsirs/ar-tafsir-ibn-kathir" },
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
  11: {
    title: "Day 11 Recitation Summary (At-Tawba 93, Yunus 26-109)",
    summary:
      "Day 11 centers on sincerity, patience, and steadfast obedience. It moves from exposing empty excuses in At-Tawba to hope, ihsan, and endurance through the closing guidance of Surah Yunus.",
    themes: [
      "Allah distinguishes real incapacity from avoidable excuse-making.",
      "Ihsan is met with immense reward, dignity, and nearness to Allah.",
      "The path forward is revelation-led patience until Allah's judgment.",
    ],
  },
  12: {
    title: "Day 12 Recitation Summary (Hud 1-123, Yusuf 1-53)",
    summary:
      "Day 12 closes Surah Hud with a sustained call to istiqamah, repentance, and trust in Allah's judgment, then opens Surah Yusuf with betrayal, patience, chastity, and eventual vindication. The recitation frames hardship as a test in which sincerity and restraint are elevated by Allah.",
    themes: [
      "The ending of Hud repeatedly commands uprightness, non-compromise with wrongdoing, and reliance on Allah.",
      "Yusuf teaches sabr jamil, moral restraint, and guarding the heart under severe personal trial.",
      "Across both surahs, relief follows sincere tawbah, taqwa, and trusting Allah's decree.",
    ],
  },
  13: {
    title: "Day 13 Recitation Summary (Yusuf 50-111, Ar-Ra'd 1-43, Ibrahim 1-52)",
    summary:
      "Day 13 closes Surah Yusuf with reunion, forgiveness, and prophetic gratitude, moves through Surah Ar-Ra'd with signs of Allah's power and the reform of the heart, then reaches the core warnings and duas of Surah Ibrahim. The recitation ties hope, remembrance, and gratitude to steadfast worship and accountability before Allah.",
    themes: [
      "Late Yusuf teaches patience rewarded, sincere forgiveness, and gratitude after relief.",
      "Ar-Ra'd repeatedly anchors faith in dhikr, tawakkul, and personal reform.",
      "Ibrahim emphasizes shukr, the danger of denial, and the lasting priority of prayer and supplication.",
    ],
  },
  14: {
    title: "Day 14 Recitation Summary (Al-Hijr 1-99, An-Nahl 1-128)",
    summary:
      "Day 14 moves from the preservation and warning themes of Surah Al-Hijr into the expansive signs, ethics, and da'wah guidance of Surah An-Nahl. The recitation emphasizes gratitude, justice, principled worship, and calling to Allah with wisdom and patience.",
    themes: [
      "Al-Hijr reinforces certainty in revelation and lifelong constancy in worship.",
      "An-Nahl repeatedly directs hearts to Allah's favors, tawhid, and accountability.",
      "The day closes with justice, wise da'wah, and Allah's support for people of taqwa and ihsan.",
    ],
  },
  15: {
    title: "Day 15 Recitation Summary (Al-Israa 1-111)",
    summary:
      "Day 15 spans all of Surah Al-Israa, moving from the Night Journey sign into a sustained program of tawhid, worship, family ethics, social justice, and accountability. The recitation repeatedly ties belief to disciplined character and reverence for revelation.",
    themes: [
      "Al-Israa centers guidance in the Quran and warns against moral drift away from revelation.",
      "The surah joins worship of Allah with lived ethics: honoring parents, guarding chastity, justice, and balanced conduct.",
      "The closing ayat renew pure tawhid, gratitude, and exaltation of Allah's greatness.",
    ],
  },
  16: {
    title: "Day 16 Recitation Summary (Maryam 1-59, Taa-Haa 26-135, Al-Anbiyaa 1-82)",
    summary:
      "Day 16 opens with Surah Maryam's scenes of mercy and prophetic devotion, moves into the mission-centered guidance of Surah Taa-Haa, and reaches the warning-and-vindication passages of Surah Al-Anbiyaa. Across both video parts, the recitation links humility, repentance, and steadfast da'wah under pressure.",
    themes: [
      "Maryam highlights purity, reverence, and the legacy of prophets who responded to revelation with humility and sujood.",
      "Taa-Haa emphasizes prophetic courage, reliance on Allah, and forgiveness for those who repent and stay guided.",
      "Early Al-Anbiyaa reinforces accountability and Allah's support for truth against persistent opposition.",
    ],
  },
  17: {
    title: "Day 17 Recitation Summary (Al-Anbiyaa 74-112, Al-Hajj 1-78, Al-Mu'minoon 1-118, An-Noor 1-20)",
    summary:
      "Day 17 moves from the closing prophetic scenes of Surah Al-Anbiyaa into the urgency and submission themes of Surah Al-Hajj, then into the character blueprint of Surah Al-Mu'minoon and the social-purity guidance at the opening of Surah An-Noor. The recitation repeatedly ties salvation to humility, disciplined worship, repentance, and moral accountability.",
    themes: [
      "Late Al-Anbiyaa emphasizes dua, repentance, and Allah's rescue of sincere prophets under trial.",
      "Al-Hajj calls to worship, striving, and communal obedience rooted in Ibrahim's legacy and tawhid.",
      "Al-Mu'minoon and early An-Noor define successful believers through purity, lowered gaze, and social responsibility.",
    ],
  },
  18: {
    title: "Day 18 Recitation Summary (An-Noor 36-64, Al-Furqan 1-77, Ash-Shu'araa 1-227)",
    summary:
      "Day 18 moves from the worship-and-purity directives in Surah An-Noor into the character and dua program of Surah Al-Furqan, then through the prophetic warning-and-resilience cycles of Surah Ash-Shu'araa. The recitation repeatedly ties honor to sincere worship, humility, repentance, and a sound heart before Allah.",
    themes: [
      "An-Noor emphasizes living faith through remembrance, obedience, and communal moral discipline.",
      "Al-Furqan defines the servants of the Most Merciful through humility, restraint, and sustained dua.",
      "Ash-Shu'araa reinforces steadfast da'wah, prophetic patience, and ultimate accountability before Allah.",
    ],
  },
  19: {
    title: "Day 19 Recitation Summary (An-Naml 1, Al-Qasas 2-88, Al-Ankaboot 1-45)",
    summary:
      "Day 19 begins with the opening ayah of Surah An-Naml, then moves through the trust, reliance, and accountability themes of Surah Al-Qasas before opening Surah Al-Ankaboot with testing, steadfast faith, and disciplined worship. The recitation repeatedly redirects the heart away from arrogance and fragile dependencies toward sincere reliance on Allah.",
    themes: [
      "The transition from An-Naml into Al-Qasas reinforces revelation-centered warning and attention to Allah's signs.",
      "Al-Qasas emphasizes divine planning, humility, and that true guidance remains in Allah's hand.",
      "Early Al-Ankaboot frames trials as a necessary filter between claim and truth in iman.",
      "The day closes by linking Quran recitation and salah to moral protection and spiritual steadiness.",
    ],
  },
  20: {
    title: "Day 20 Recitation Summary (Al-Ankaboot 46-69, Ar-Rum, Luqman, As-Sajdah, Al-Ahzab, Saba 1-54)",
    summary:
      "Day 20 moves through signs of Allah in creation, disciplined worship, and prophetic-centered devotion, then closes with accountability and the collapse of false certainty in Saba. The recitation repeatedly links inner reform to truthful speech, steady remembrance, and trust in Allah's decree.",
    themes: [
      "Daily dhikr, salah, and patience are presented as the practical framework for spiritual stability.",
      "Family ethics, community character, and public speech are tied directly to taqwa.",
      "True honor and safety come through obedience, salawat, and reliance on Allah alone.",
    ],
  },
  21: {
    title: "Day 21 Recitation Summary (Fatir 1-45, Ya-Sin 1-83, As-Saffat 1-182, Sad 1-88, Az-Zumar 1-31)",
    summary:
      "Day 21 moves from divine power and human dependence in Fatir into resurrection certainty and Quranic warning in Ya-Sin, then through prophetic devotion and sacrifice in As-Saffat and Sad, before reaching sincerity, repentance, and revelation-centered transformation in Az-Zumar. The recitation repeatedly calls the heart to tawhid, humility, and accountability before Allah.",
    themes: [
      "Creation signs and resurrection scenes are used to restore certainty in Allah's power and final return.",
      "Prophetic duas and stories model patience, sacrifice, repentance, and steadfast worship under trial.",
      "Az-Zumar emphasizes ikhlas, fear-and-hope balance, and deep receptivity to the Quran as the path to reform.",
    ],
  },
  22: {
    title: "Day 22 Recitation Summary (Az-Zumar 60-75, Ghafir 1-85, Fussilat 1-54, Ash-Shuraa 1-38)",
    summary:
      "Day 22 closes Az-Zumar with decisive scenes of judgment and salvation, then moves through Ghafir with the call to repentance, tawakkul, and certainty in resurrection. It continues through Fussilat with steadfast witness and Quran-centered guidance, and reaches Ash-Shuraa's foundations of tawhid, dependence, and shura-guided community life.",
    themes: [
      "Accountability scenes in Az-Zumar and Ghafir renew fear, hope, and urgency in repentance.",
      "Believers are trained to combine dua, trust, and principled speech under pressure.",
      "Fussilat and Ash-Shuraa anchor steadfastness, Allah-centered reliance, and faithful communal conduct.",
    ],
  },
  23: {
    title: "Day 23 Recitation Summary (Az-Zukhruf 1-89, Ad-Dukhan 1-59, Al-Jathiyah 1-37, Al-Ahqaf 1-35, Muhammad 1-38, Al-Fath 1-29)",
    summary:
      "Day 23 moves from revelation, tawhid, and the critique of worldly arrogance in Az-Zukhruf into warning and accountability scenes in Ad-Dukhan and Al-Jathiyah. It then carries the heart through repentance and steadfast warning in Al-Ahqaf, disciplined commitment in Muhammad, and the victory-and-pledge framework of Al-Fath. The recitation repeatedly ties honor to obedience, sincerity, and trust in Allah's decree.",
    themes: [
      "Revelation is presented as criterion, exposing false pride and calling people back to sincere worship.",
      "Scenes of judgment, repentance, and the fate of rejecting nations renew fear-and-hope balance.",
      "Al-Fath closes with prophetic loyalty, mercy among believers, and a disciplined path to victory.",
    ],
  },
  24: {
    title: "Day 24 Recitation Summary (Al-Hujurat 1-18, Qaf 1-45, Adh-Dhariyat 1-60, At-Tur 1-49, An-Najm 1-62, Al-Qamar 1-55, Ar-Rahman 1-78, Al-Waqiah 1-96, Al-Hadid 1-29)",
    summary:
      "Day 24 moves from disciplined speech and communal adab in Al-Hujurat into accountability and inner awareness in Qaf, then through worship-centered purpose and yaqeen in Adh-Dhariyat. It continues with warning-and-certainty passages in At-Tur, An-Najm, and Al-Qamar, before the gratitude refrains of Ar-Rahman, the akhirah sorting of Al-Waqiah, and the spending-and-sincerity framework in Al-Hadid.",
    themes: [
      "Believer character is framed through adab, humility, and guarding speech before Allah and His Messenger.",
      "Repeated akhirah scenes and signs in creation renew fear, hope, and certainty in resurrection.",
      "The day closes by tying true honor to worship, generosity, and iman-rooted action.",
    ],
  },
  25: {
    title: "Day 25 Recitation Summary (Al-Mujadilah 11-22, Al-Hashr 1-24, Al-Mumtahanah 1-13, As-Saff 1-14, Al-Jumuah 1-11, Al-Munafiqun 1-11)",
    summary:
      "Day 25 centers on loyal faith identity, truthful obedience, and disciplined remembrance. It moves from adab and sincere allegiance in Al-Mujadilah and Al-Hashr into tests of love, alliance, and prophetic example in Al-Mumtahanah, then through mission integrity in As-Saff, Jumuah-priority worship in Al-Jumuah, and final warnings against heedless distraction in Al-Munafiqun.",
    themes: [
      "The recitation links elevated rank to iman, knowledge, and obedience-based adab.",
      "Believers are repeatedly called to align public claims with sincere, actionable commitment.",
      "The day closes by prioritizing dhikr and worship over worldly distraction and delay.",
    ],
  },
  26: {
    title: "Day 26 Recitation Summary (At-Taghabun 1-18, At-Talaq 1-12, At-Tahrim 1-12, Al-Mulk 1-30, Al-Qalam 1-52, Al-Haqqah 1-52, Al-Ma'arij 1-35)",
    summary:
      "Day 26 moves through disciplined taqwa and tawakkul in At-Taghabun and At-Talaq, then through repentance and household sincerity in At-Tahrim. It continues with accountability-centered reflections in Al-Mulk, steadfast prophetic character in Al-Qalam, and akhirah certainty in Al-Haqqah and Al-Ma'arij, repeatedly calling the heart to truthful obedience and preparation for return to Allah.",
    themes: [
      "Taqwa is tied to practical obedience, trust in Allah, and ethical consistency under pressure.",
      "The recitation repeatedly contrasts sincere repentance and steadfastness with heedlessness and delay.",
      "Akhirah scenes in Al-Haqqah and Al-Ma'arij sharpen urgency for worship, patience, and reform.",
    ],
  },
  27: {
    title: "Day 27 Recitation Summary (Al-Ma'arij 36-44, Nuh 1-28, Al-Jinn 1-28, Al-Muzzammil 1-20, Al-Muddaththir 1-56, Al-Qiyamah 1-40, Al-Insan 1-31, Al-Mursalat 1-50, An-Naba 1-40, An-Naziat 1-46, Abasa 1-42)",
    summary:
      "Day 27 moves through urgent akhirah warnings in the close of Al-Ma'arij, repentance and da'wah persistence in Nuh, and obedience-centered reform across Al-Jinn, Al-Muzzammil, and Al-Muddaththir. It continues through accountability scenes in Al-Qiyamah, gratitude and sincerity in Al-Insan, and powerful resurrection imagery through Al-Mursalat, An-Naba, An-Naziat, and Abasa. The recitation repeatedly calls for disciplined worship, moral seriousness, and preparation for the final standing before Allah.",
    themes: [
      "Persistent repentance, recitation, and prayer are framed as the path to steadfastness.",
      "Akhirah imagery repeatedly dismantles heedlessness and resets priorities.",
      "Personal accountability and self-restraint are presented as keys to salvation.",
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
