# Census 2025 Weighted Data Dictionary

- Source file: `/Users/peter/Downloads/census2025_cleaned_weighted.xlsx`
- Sheet: `census2025_cleaned_weighted`
- Rows: `5028`
- Columns: `343`

Columns:

| column | dtype | missing | missing_pct | unique | sample_values |
|---|---|---|---|---|---|
| responseID | int64 | 0 | 0.00% | 5028 | 32; 34; 36 |
| timeStarted | datetime64[us] | 0 | 0.00% | 5009 | 2025-08-30 15:24:02; 2025-08-30 15:35:30; 2025-08-30 15:58:31 |
| dateSubmitted | datetime64[us] | 0 | 0.00% | 5018 | 2025-08-30 15:57:55; 2025-08-30 15:48:34; 2025-08-30 16:11:08 |
| status | str | 0 | 0.00% | 1 | Complete |
| legacyComments | float64 | 5028 | 100.00% | 0 |  |
| comments | float64 | 5028 | 100.00% | 0 |  |
| language | str | 0 | 0.00% | 1 | English |
| referer | str | 0 | 0.00% | 137 | https://burningman.org/; https://www.sfchronicle.com/entertainment/article/burning-man-2025-census-demographics-21024... |
| sessionID | str | 0 | 0.00% | 5028 | 1756592566_68b379b62bd842.96893525; 1756593295_68b37c8f91dbf2.64807765; 1756594703_68b3820f32ac23.16244537 |
| userAgent | float64 | 5028 | 100.00% | 0 |  |
| tags | float64 | 5028 | 100.00% | 0 |  |
| authorization | int64 | 0 | 0.00% | 1 | 3 |
| authorization2 | float64 | 51 | 1.01% | 2 | 1.0; 2.0 |
| virgin | str | 0 | 0.00% | 2 | virgin; not virgin |
| atBRC | str | 17 | 0.34% | 2 | no; yesStillThere |
| age | int64 | 0 | 0.00% | 69 | 28; 57; 36 |
| virgin.1 | str | 0 | 0.00% | 2 | virgin; not virgin |
| reside | str | 4 | 0.08% | 5 | otherUS; California; Nevada |
| reside.otherCountry.writeIn | object | 4522 | 89.94% | 140 | Germany; Sweden; Italy |
| resideZIP | float64 | 795 | 15.81% | 1899 | 83706.0; 94709.0; 94568.0 |
| resideCAPostalCode | object | 4873 | 96.92% | 151 | T2L2M4; V5z3h9; K1n6v2 |
| attendedYears.2025 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2024 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2023 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2022 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2019 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2018 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2017 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2016 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2015 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2014 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2013 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2012 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2011 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2010 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2009 | float64 | 1248 | 24.82% | 2 | 1.0; 0.0 |
| attendedYears.2008 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.2007 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.2006 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.2005 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.2004 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.2003 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.2002 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.2001 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.2000 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1999 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1998 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1997 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1996 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1995 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1994 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1993 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1992 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1991 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1990BlackRock | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1990Baker | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1989 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1988 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1987 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| attendedYears.1986 | float64 | 1248 | 24.82% | 2 | 0.0; 1.0 |
| regionalsNumberAttended | str | 12 | 0.24% | 3 | never; multipleTimes; once |
| gender | str | 17 | 0.34% | 3 | male; female; selfDescribe |
| gender.selfDescribe.writeIn | str | 4910 | 97.65% | 59 | Two spirit; nonbinary; Non-binary |
| race.nativeAmericanAlaskan | float64 | 27 | 0.54% | 2 | 0.0; 1.0 |
| race.asian | float64 | 27 | 0.54% | 2 | 0.0; 1.0 |
| race.black | float64 | 27 | 0.54% | 2 | 0.0; 1.0 |
| race.nativeHawaiianPacificIslander | float64 | 27 | 0.54% | 2 | 0.0; 1.0 |
| race.white | float64 | 27 | 0.54% | 2 | 1.0; 0.0 |
| race.middleEasternNorthAfrican | float64 | 27 | 0.54% | 2 | 0.0; 1.0 |
| race.hispanic | float64 | 27 | 0.54% | 2 | 1.0; 0.0 |
| race.other | float64 | 27 | 0.54% | 2 | 0.0; 1.0 |
| race.other.writeIn | str | 4886 | 97.18% | 91 | Mixed; Jewish; Hispanic, African American, Native, White |
| personalIncome | str | 73 | 1.45% | 13 | 75000to99999; 150000to299999; 100000to149999 |
| householdIncludeOthers | str | 23 | 0.46% | 2 | no; yes |
| householdIncludeOthers.1 | str | 23 | 0.46% | 2 | no; yes |
| education | str | 9 | 0.18% | 9 | bachelors; masters; doctorate |
| education.other.writeIn | str | 5010 | 99.64% | 18 | Bac plus 5 en France  DESS; BA and BS (2); Bachelor's of Architecture (5 year), and some Graduate school |
| voteInLastElection | str | 11 | 0.22% | 3 | yes; notEligible; no |
| ticketSale | str | 5 | 0.10% | 4 | standardTicket; other; staffOrVolunteer |
| voteLastFourUS.2024 | float64 | 711 | 14.14% | 2 | 1.0; 0.0 |
| voteLastFourUS.2022 | float64 | 711 | 14.14% | 2 | 1.0; 0.0 |
| voteLastFourUS.2020 | float64 | 711 | 14.14% | 2 | 1.0; 0.0 |
| voteLastFourUS.2018 | float64 | 711 | 14.14% | 2 | 0.0; 1.0 |
| voteLastFourUS.none | float64 | 711 | 14.14% | 2 | 0.0; 1.0 |
| voteLastFourUS.notEligible | float64 | 711 | 14.14% | 2 | 0.0; 1.0 |
| politicalPartyUS | str | 981 | 19.51% | 7 | democratic; libertarian; noneUnaffiliated |
| politicalPartyUS.otherUSPoliticalParty.writeIn | str | 4978 | 99.01% | 31 | Socialist; Democratic socialist; Unaffiliated |
| politicalViews.anarchist | float64 | 50 | 0.99% | 2 | 0.0; 1.0 |
| politicalViews.conservative | float64 | 50 | 0.99% | 2 | 0.0; 1.0 |
| politicalViews.green | float64 | 50 | 0.99% | 2 | 0.0; 1.0 |
| politicalViews.liberal | float64 | 50 | 0.99% | 2 | 0.0; 1.0 |
| politicalViews.libertarian | float64 | 50 | 0.99% | 2 | 0.0; 1.0 |
| politicalViews.moderate | float64 | 50 | 0.99% | 2 | 1.0; 0.0 |
| politicalViews.progressive | float64 | 50 | 0.99% | 2 | 0.0; 1.0 |
| politicalViews.socialist | float64 | 50 | 0.99% | 2 | 0.0; 1.0 |
| politicalViews.other | float64 | 50 | 0.99% | 2 | 0.0; 1.0 |
| politicalViews.noneApolitical | float64 | 50 | 0.99% | 2 | 0.0; 1.0 |
| politicalViews.preferNotToState | float64 | 50 | 0.99% | 2 | 0.0; 1.0 |
| politicalViews.other.writeIn | str | 4933 | 98.11% | 78 | Abolitionist; anti-woke civic nationalist and neoKeynesian; Leftist |
| language.1 | str | 11 | 0.22% | 23 | english; urdu; other |
| language.other.writeIn | str | 4904 | 97.53% | 53 | vietnamese; Vietnamese; Albanian |
| spirituality | str | 20 | 0.40% | 6 | agnostic; dontKnow; spiritual |
| sexualOrientation | str | 19 | 0.38% | 7 | heterosexualStraight; bisexualPansexual; bicuriousHeteroflexible |
| sexualOrientation.selfDescribe.writeIn | str | 4973 | 98.91% | 26 | Demisexual; Queer; queer |
| genderIdentity | str | 28 | 0.56% | 2 | no; yes |
| partner | str | 19 | 0.38% | 4 | no; yesMarried; yesNotMarried |
| petsAny | str | 8 | 0.16% | 4 | no; yesMultiple; yesOne |
| petsWhatKind.cats | float64 | 2097 | 41.71% | 2 | 0.0; 1.0 |
| petsWhatKind.dogs | float64 | 2097 | 41.71% | 2 | 1.0; 0.0 |
| petsWhatKind.birdsPoultry | float64 | 2097 | 41.71% | 2 | 0.0; 1.0 |
| petsWhatKind.fishCrustaceans | float64 | 2097 | 41.71% | 2 | 0.0; 1.0 |
| petsWhatKind.rabbitsRodents | float64 | 2097 | 41.71% | 2 | 0.0; 1.0 |
| petsWhatKind.reptilesAmphibians | float64 | 2097 | 41.71% | 2 | 0.0; 1.0 |
| petsWhatKind.instectsArachnids | float64 | 2097 | 41.71% | 2 | 0.0; 1.0 |
| petsWhatKind.goatsSheep | float64 | 2097 | 41.71% | 2 | 0.0; 1.0 |
| petsWhatKind.horses | float64 | 2097 | 41.71% | 2 | 0.0; 1.0 |
| petsWhatKind.otherFarmAnimals | float64 | 2097 | 41.71% | 2 | 0.0; 1.0 |
| petsWhatKind.other | float64 | 2097 | 41.71% | 2 | 0.0; 1.0 |
| petsWhatKind.otherFarmAnimals.writeIn | str | 5003 | 99.50% | 20 | Donkeys; Alpaca; Cows |
| petsWhatKind.other.writeIn | str | 5003 | 99.50% | 25 | We have a T. Rex; dog died 1 month before Burning Man; All |
| mediaManagedByBMP.jackrabbitSpeaks | str | 84 | 1.67% | 3 | Never; Rarely; Often |
| mediaManagedByBMP.burningManWebsite | str | 131 | 2.61% | 3 | Often; Rarely; Never |
| mediaManagedByBMP.burningManJournal | str | 279 | 5.55% | 3 | Never; Rarely; Often |
| mediaManagedByBMP.burningManHive | str | 334 | 6.64% | 3 | Never; Rarely; Often |
| mediaManagedByBMP.socialMedia | str | 170 | 3.38% | 3 | Often; Rarely; Never |
| mediaManagedByBMP.ePlaya | str | 368 | 7.32% | 3 | Never; Rarely; Often |
| preparationResourcesFromBMP.survivalGuideBooklet | float64 | 390 | 7.76% | 2 | 1.0; 0.0 |
| preparationResourcesFromBMP.onlineSurvivalGuide | float64 | 390 | 7.76% | 2 | 1.0; 0.0 |
| preparationResourcesFromBMP.website | float64 | 390 | 7.76% | 2 | 1.0; 0.0 |
| preparationResourcesFromBMP.instagram | float64 | 390 | 7.76% | 2 | 0.0; 1.0 |
| preparationResourcesFromBMP.facebook | float64 | 390 | 7.76% | 2 | 0.0; 1.0 |
| preparationResourcesFromBMP.tiktok | float64 | 390 | 7.76% | 2 | 0.0; 1.0 |
| preparationResourcesFromBMP.youtube | float64 | 390 | 7.76% | 2 | 0.0; 1.0 |
| preparationResourcesFromBMP.journal | float64 | 390 | 7.76% | 2 | 0.0; 1.0 |
| preparationResourcesFromBMP.LIVEPodcast | float64 | 390 | 7.76% | 2 | 0.0; 1.0 |
| preparationResourcesFromBMP.jackrabbitSpeaks | float64 | 390 | 7.76% | 2 | 0.0; 1.0 |
| preparationResourcesFromBMP.HIVE | float64 | 390 | 7.76% | 2 | 0.0; 1.0 |
| preparationResourcesFromBMP.other | float64 | 390 | 7.76% | 2 | 1.0; 0.0 |
| preparationResourcesFromBMP.other.writeIn | str | 4316 | 85.84% | 490 | Reddit; Bmir; Dust app |
| valuableInformationFromBMP.eventsInBRC | float64 | 308 | 6.13% | 2 | 1.0; 0.0 |
| valuableInformationFromBMP.bayAreaEvents | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.eventsInOtherCities | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.regionals | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.volunteerOpportunities | float64 | 308 | 6.13% | 2 | 1.0; 0.0 |
| valuableInformationFromBMP.artOpportunities | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.preparationInformation | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.campInformation | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.photosFromBRC | float64 | 308 | 6.13% | 2 | 1.0; 0.0 |
| valuableInformationFromBMP.storiesAboutBurners | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.nonProfitInformation | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.RIDEInformation | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.sustainability | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.other | float64 | 308 | 6.13% | 2 | 0.0; 1.0 |
| valuableInformationFromBMP.other.writeIn | str | 4946 | 98.37% | 82 | Ingenuity; I think the environmental sustainability of BM is overstated - it's not an environmentally friendly event;... |
| radio.BMIR | float64 | 67 | 1.33% | 2 | 1.0; 0.0 |
| radio.GARS | float64 | 67 | 1.33% | 2 | 1.0; 0.0 |
| radio.other | float64 | 67 | 1.33% | 2 | 0.0; 1.0 |
| radio.none | float64 | 67 | 1.33% | 2 | 0.0; 1.0 |
| radio.other.writeIn | object | 4927 | 97.99% | 79 | 91.5 KLAP; Electra; GARS was unusable, signal so weak you had to be PAST the gate to hear it |
| devicesUsedAtBRC.thirdPartyBRCApp | str | 87 | 1.73% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.BRCDashboard | str | 151 | 3.00% | 4 | Less than once per day; About once a day; More than once a day |
| devicesUsedAtBRC.contentCapture | str | 103 | 2.05% | 4 | Never; About once a day; More than once a day |
| devicesUsedAtBRC.sharingSocialMedia | str | 144 | 2.86% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.browsingSocialMedia | str | 146 | 2.90% | 4 | Never; Less than once per day; About once a day |
| devicesUsedAtBRC.contactBurnersAtBRC | str | 136 | 2.70% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.contactPeopleOutsideBRC | str | 125 | 2.49% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.checkWorkEmails | str | 127 | 2.53% | 4 | Never; More than once a day; About once a day |
| devicesUsedAtBRC.checkPersonalEmails | str | 112 | 2.23% | 4 | Never; Less than once per day; About once a day |
| devicesUsedAtBRC.saveNewConnections | str | 138 | 2.74% | 4 | Never; About once a day; Less than once per day |
| devicesUsedAtBRC.playMusic | str | 125 | 2.49% | 4 | Never; About once a day; Less than once per day |
| devicesUsedAtBRC.streamVideosMovies | str | 150 | 2.98% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.readNews | str | 145 | 2.88% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.thirdPartyBRCApp.1 | str | 87 | 1.73% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.BRCDashboard.1 | str | 151 | 3.00% | 4 | Less than once per day; About once a day; More than once a day |
| devicesUsedAtBRC.contentCapture.1 | str | 103 | 2.05% | 4 | Never; About once a day; More than once a day |
| devicesUsedAtBRC.sharingSocialMedia.1 | str | 144 | 2.86% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.browsingSocialMedia.1 | str | 146 | 2.90% | 4 | Never; Less than once per day; About once a day |
| devicesUsedAtBRC.contactBurnersAtBRC.1 | str | 136 | 2.70% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.contactPeopleOutsideBRC.1 | str | 125 | 2.49% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.checkWorkEmails.1 | str | 127 | 2.53% | 4 | Never; More than once a day; About once a day |
| devicesUsedAtBRC.checkPersonalEmails.1 | str | 112 | 2.23% | 4 | Never; Less than once per day; About once a day |
| devicesUsedAtBRC.saveNewConnections.1 | str | 138 | 2.74% | 4 | Never; About once a day; Less than once per day |
| devicesUsedAtBRC.playMusic.1 | str | 125 | 2.49% | 4 | Never; About once a day; Less than once per day |
| devicesUsedAtBRC.streamVideosMovies.1 | str | 150 | 2.98% | 4 | Never; Less than once per day; More than once a day |
| devicesUsedAtBRC.readNews.1 | str | 145 | 2.88% | 4 | Never; Less than once per day; More than once a day |
| burnerIdentity | str | 5 | 0.10% | 3 | sortOf; no; yes |
| connectedToBurnerCommunity | str | 5 | 0.10% | 5 | slightlyConnected; veryConnected; mdoeratelyConnected |
| regionalInvolved.production | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.staffVolunteer | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.meetings | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.medical | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.art | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.themeCamp | float64 | 2958 | 58.83% | 2 | 1.0; 0.0 |
| regionalInvolved.vendor | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.performance | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.donor | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.supporter | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.other | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.notInvolved | float64 | 2958 | 58.83% | 2 | 0.0; 1.0 |
| regionalInvolved.other.writeIn | str | 4933 | 98.11% | 66 | Attendee; new to BM; Participant |
| interestBurningManCommunity | str | 17 | 0.34% | 5 | probablyInterested; absolutelyNotInterested; absolutelyInterested |
| interestBurningManCommunity.1 | str | 17 | 0.34% | 5 | probablyInterested; absolutelyNotInterested; absolutelyInterested |
| charitableDonation.burningManProject | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.Regional | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.burnersWithoutBorders | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.flyRanch | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.artPojects | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.politicalCampaignsVoterRegistration | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.schoolsUniversities | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.animalsEnvironmentalInitiatives | float64 | 1305 | 25.95% | 2 | 1.0; 0.0 |
| charitableDonation.healthInitiatives | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.humanRightsInitiatives | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.povertyInitiatives | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.religiousInitiatives | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.communityGroupsClubs | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.selfInitiatedGoodDeeds | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.otherNonprofitsCharities | float64 | 1305 | 25.95% | 2 | 0.0; 1.0 |
| charitableDonation.otherNonprofits.writeIn | str | 4658 | 92.64% | 328 | World central kitchen; Human Rights; Other non profits |
| tenPrinciplesHowImportant | str | 19 | 0.38% | 6 | important; notImportant; veryImportant |
| tenPrinciplesWhichImportant.radicalInclusion | bool | 0 | 0.00% | 1 | True |
| tenPrinciplesWhichImportant.gifting | bool | 0 | 0.00% | 1 | True |
| tenPrinciplesWhichImportant.decommodification | bool | 0 | 0.00% | 1 | True |
| tenPrinciplesWhichImportant.radicalSelfReliance | bool | 0 | 0.00% | 1 | True |
| tenPrinciplesWhichImportant.radicalSelfExpression | bool | 0 | 0.00% | 1 | True |
| tenPrinciplesWhichImportant.communalEffort | bool | 0 | 0.00% | 1 | True |
| tenPrinciplesWhichImportant.civicResponsibility | bool | 0 | 0.00% | 1 | True |
| tenPrinciplesWhichImportant.leaveNoTrace | bool | 0 | 0.00% | 1 | True |
| tenPrinciplesWhichImportant.participation | bool | 0 | 0.00% | 1 | True |
| tenPrinciplesWhichImportant.immediacy | bool | 0 | 0.00% | 1 | True |
| tenPrinciplesDailyLife | str | 18 | 0.36% | 3 | yes; no; sortOf |
| arrivedDate | str | 15 | 0.30% | 16 | event0; event4; event2 |
| leaveDate | str | 20 | 0.40% | 14 | event6; event5; post8 |
| arrivePoint | str | 18 | 0.36% | 6 | gateInVehicle; point1; gateInBXB |
| arrivePoint.other.writeIn | str | 5013 | 99.70% | 15 | We tunneled in; through gate with dept/org truck; 12 mile road gate with an artist |
| arrivePoint.1 | str | 18 | 0.36% | 6 | gateInVehicle; point1; gateInBXB |
| arrivePoint.other.writeIn.1 | str | 5013 | 99.70% | 15 | We tunneled in; through gate with dept/org truck; 12 mile road gate with an artist |
| rideBike | str | 7 | 0.14% | 3 | yesRegularBike; yesEbike; no |
| spendTravelBRC | float64 | 297 | 5.91% | 228 | 1200.0; 300.0; 700.0 |
| spendTravelBRC.1 | float64 | 297 | 5.91% | 228 | 1200.0; 300.0; 700.0 |
| campAddressStreet | str | 15 | 0.30% | 15 | H; dontRemember; A |
| campCenterCampRadial | str | 4982 | 99.09% | 6 | f; a; c |
| campStreetSide | str | 711 | 14.14% | 2 | closerToEsplanade; fartherFromEsplanade |
| campKStreetSide | str | 4877 | 97.00% | 2 | fartherFromEsplanade; closerToEsplanade |
| campAddressStreet.1 | str | 15 | 0.30% | 15 | H; dontRemember; A |
| campPlaced | str | 15 | 0.30% | 3 | dontKnow; yes; no |
| reduceEnvironmentalImpact.memberOfSustainableCamp | float64 | 56 | 1.11% | 2 | 0.0; 1.0 |
| reduceEnvironmentalImpact.usedRenewableEnergy | float64 | 56 | 1.11% | 2 | 0.0; 1.0 |
| reduceEnvironmentalImpact.wasteReductionPlan | float64 | 56 | 1.11% | 2 | 1.0; 0.0 |
| reduceEnvironmentalImpact.minimizedFoodWaste | float64 | 56 | 1.11% | 2 | 1.0; 0.0 |
| reduceEnvironmentalImpact.collectedGreywater | float64 | 56 | 1.11% | 2 | 0.0; 1.0 |
| reduceEnvironmentalImpact.reducedPlastic | float64 | 56 | 1.11% | 2 | 1.0; 0.0 |
| reduceEnvironmentalImpact.leaveNoTrace | float64 | 56 | 1.11% | 2 | 1.0; 0.0 |
| reduceEnvironmentalImpact.helpedOthersLearn | float64 | 56 | 1.11% | 2 | 0.0; 1.0 |
| reduceEnvironmentalImpact.cansToRecycleCamp | float64 | 56 | 1.11% | 2 | 0.0; 1.0 |
| reduceEnvironmentalImpact.other | float64 | 56 | 1.11% | 2 | 0.0; 1.0 |
| reduceEnvironmentalImpact.none | float64 | 56 | 1.11% | 2 | 0.0; 1.0 |
| reduceEnvironmentalImpact.other.writeIn | str | 4809 | 95.64% | 217 | 5 gallon sponge baths; Brought recycling home to recycle in Oregon; Brought trash and recycling to bxb depot |
| createDiversity.welcomedUnderRepresentedGroups | float64 | 440 | 8.75% | 2 | 0.0; 1.0 |
| createDiversity.financialAssistance | float64 | 440 | 8.75% | 2 | 0.0; 1.0 |
| createDiversity.other | float64 | 440 | 8.75% | 2 | 0.0; 1.0 |
| createDiversity.none | float64 | 440 | 8.75% | 2 | 1.0; 0.0 |
| createDiversity.other.writeIn | str | 4679 | 93.06% | 347 | Welcomed everyone equally; Feeding burners; International camp |
| attendChallenge | str | 43 | 0.86% | 8 | learning; noChallenge; transportation |
| attendChallenge.other.writeIn | str | 4514 | 89.78% | 486 | Camp drama; Finding an RV to rent that wasn't anti-burning man; Arranging child care |
| attendNextYear | str | 17 | 0.34% | 5 | probably; absolutelyNot; absolutely |
| attendTwoOrMoreYears | str | 15 | 0.30% | 5 | probably; probablyNot; absolutely |
| reasonToReturnToBRC. | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.seeExperienceArt | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.createWorkOnProject | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.likeMindedPeopleBelonging | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.meetPeopleDifferentFromMe | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.playExperienceFreedom | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.consumeIntoxicants | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.escapeWorld | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.expressMyself | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.giftingDecommodication | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.relyOnMyselfPracticeSkills | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.performPracticeArtSkills | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.curiosityBucketList | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.growConnectSpiritually | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.satisfySomeoneElse | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.other | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.other.writeIn | str | 4823 | 95.92% | 204 | Continuing to learn new things about surviving in disaster-like zone and apply innovative ideas in the default world;... |
| reasonToReturnToBRC..1 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.seeExperienceArt.1 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.createWorkOnProject.1 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.likeMindedPeopleBelonging.1 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.meetPeopleDifferentFromMe.1 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.playExperienceFreedom.1 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.consumeIntoxicants.1 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.escapeWorld.1 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.expressMyself.1 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.giftingDecommodication.1 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.relyOnMyselfPracticeSkills.1 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.performPracticeArtSkills.1 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.curiosityBucketList.1 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.growConnectSpiritually.1 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.satisfySomeoneElse.1 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.other.1 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.other.writeIn.1 | str | 4823 | 95.92% | 204 | Continuing to learn new things about surviving in disaster-like zone and apply innovative ideas in the default world;... |
| reasonToReturnToBRC..2 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.seeExperienceArt.2 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.createWorkOnProject.2 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.likeMindedPeopleBelonging.2 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.meetPeopleDifferentFromMe.2 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.playExperienceFreedom.2 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.consumeIntoxicants.2 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.escapeWorld.2 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.expressMyself.2 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.giftingDecommodication.2 | float64 | 79 | 1.57% | 2 | 1.0; 0.0 |
| reasonToReturnToBRC.relyOnMyselfPracticeSkills.2 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.performPracticeArtSkills.2 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.curiosityBucketList.2 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.growConnectSpiritually.2 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.satisfySomeoneElse.2 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.other.2 | float64 | 79 | 1.57% | 2 | 0.0; 1.0 |
| reasonToReturnToBRC.other.writeIn.2 | str | 4823 | 95.92% | 204 | Continuing to learn new things about surviving in disaster-like zone and apply innovative ideas in the default world;... |
| dataNerds | str | 14 | 0.28% | 2 | yes; no |
| playaNameUse | str | 343 | 6.82% | 2 | no; yes |
| playaNameAcquire | str | 2528 | 50.28% | 4 | givenToMeParticipant; other; choseItMyself |
| playaNameAcquire.other.writeIn | str | 4884 | 97.14% | 142 | Burning man ranger assigned; Nick name my friends use.; I tried on a different version of my given name (""""Kath""""... |
| playaNameYears | str | 2531 | 50.34% | 2 | usedMultipleYears; startedThisYear |
| playaNameYears.numberOfYearsUsed.writeIn | object | 3274 | 65.12% | 174 | 15; 2; 4 |
| playaNameEffect.reflectDefaultIdentity | str | 2541 | 50.54% | 5 | Very much; Slightly; Extremely |
| playaNameEffect.reflectUnusualIdentity | str | 2562 | 50.95% | 5 | Not at all; Moderately; Slightly |
| playaNameEffect.reflectDailyLife | str | 2559 | 50.89% | 5 | Very much; Not at all; Extremely |
| playaNameEffect.enchanceOthersPerception | str | 2562 | 50.95% | 5 | Very much; Not at all; Extremely |
| playaNameEffect.freeOfStigma | str | 2572 | 51.15% | 5 | Not at all; Extremely; Moderately |
| playaNameEffect.beMoreEngagedPresent | str | 2567 | 51.05% | 5 | Moderately; Not at all; Extremely |
| playaNameEffect.maintainPrivacy | str | 2568 | 51.07% | 5 | Slightly; Not at all; Extremely |
| playaNameEffect.feelComfortableCommunicating | str | 2569 | 51.09% | 5 | Moderately; Slightly; Extremely |
| artMakingContribute.yesContributedMaterial | float64 | 373 | 7.42% | 2 | 0.0; 1.0 |
| artMakingContribute.yesContributedDigital | float64 | 373 | 7.42% | 2 | 0.0; 1.0 |
| artMakingContribute.yesContributedPerformative | float64 | 373 | 7.42% | 2 | 0.0; 1.0 |
| artMakingContribute.yesContributedOther | float64 | 373 | 7.42% | 2 | 0.0; 1.0 |
| artMakingContribute.no | float64 | 373 | 7.42% | 2 | 1.0; 0.0 |
| artMakingContribute.yesIContributedToAnotherArtForm.writeIn | str | 4522 | 89.94% | 457 | Electronics for distributed Spatial Audio; Theme camp activity creation; Art car team |
| artMakingImportance | str | 372 | 7.40% | 5 | veryImportant; notImportant; mostImportant |
| artMakingAvenue | str | 372 | 7.40% | 3 | noVenue; yes; no |
| artMakingFriends | str | 399 | 7.94% | 2 | no; yes |
| artMakingCollaborate | str | 389 | 7.74% | 2 | no; yes |
| nburns | float64 | 2 | 0.04% | 31 | 1.0; 15.0; 4.0 |
| weights | float64 | 0 | 0.00% | 1419 | 0.617320008066036; 1.97882928189255; 0.50889913906688 |