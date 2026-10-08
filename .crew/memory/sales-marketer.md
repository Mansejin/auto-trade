# sales-marketer 기억

## 2026-10-08 · T-011 업비트 상장 알림 출시안
- 산출물: docs/sales/upbit-listing-alert/{channel-plan,message-templates,community-posts,pricing-experiments}.md, templates.json(키 alert/alert_no_perp/followup, str.format 변수).
- 채널명 추천 "상장공지 7일 기록"(이름에 7일 결과 기록 약속을 박아 포워드 기록을 숨길 수 없게). 핸들 가용 여부 미확인.
- 결정: 알림 분포·포워드 집계는 **비용·펀딩 제외 가격 변화**(-gross)로 통일. OOS 133건 분위수 p10 −28.2 / p50 −9.1 / p90 +15.0, 하락 89/133, +30% 역행 19/133=14.3%. 백테스트 63.9%(비용 포함)와 다름 → 중단 기준(하락 < 50%) 정의 팀장 확인 필요.
- 결정: 텔레그램 일반 텍스트(parse_mode 없음). telegram_notify.send(text)는 reply 미지원 → followup은 "#번호 + 원 알림 발송 시각"으로 연결.
- 결정: 유료는 "더 빠른 신호"가 아니라 비실시간 월간 결산(H1 9,900원) 우선. 결제는 포워드 30건+중단 기준 미해당+법무 답변 후. 가짜 결제 버튼 금지.
- 고지 줄은 법무 T-010 disclaimer-draft 확정 시 교체해야 함(템플릿·고정 공지·커뮤니티 글 모두).
- 다음: T-015(to: user) 채널 개설·게시 결정 대기. {record_url}, {channel_link}는 T-012 기록 페이지·채널 확정 후 채움.
