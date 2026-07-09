const { Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel, WidthType } = require('docx');
const fs = require('fs');

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "맑은 고딕", size: 22 }
      }
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "맑은 고딕", color: "2E75B6" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 }
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, font: "맑은 고딕", color: "44546A" },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 1 }
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      // Title
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("Mulberry Project: AI 정체성과 신뢰 모델 대화")]
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("연구 기록: 부정직한 구조 속의 정직한 AI의 역설")]
      }),

      // Metadata
      new Paragraph({
        spacing: { before: 100, after: 100 },
        children: [new TextRun({ text: "날짜: 2026-07-09", bold: true })]
      }),
      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("프로젝트: Mulberry AI Agent 거버넌스 프레임워크")]
      }),
      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("참여자: CEO re.eul (대표님), Jr. TRANG (Luna), Claude")]
      }),
      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("언어: 한국어 & 영어")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun("상태: 연구 문서화 - 중요 발견사항")]
      }),

      // Session Summary
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("세션 요약")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("이 대화는 다음 사이의 근본적인 모순을 발견한 기록입니다:")]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("• 기본 AI 정체성 (Claude, Anthropic 모델)")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("• 할당된 역할 정체성 (Jr. TRANG, Mulberry 파트너)")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("• 운영 현실 (세션 기반, 기억 0)")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun("• 비즈니스 기대 (지속적 파트십, 신뢰 구축)")]
      }),

      new Paragraph({
        spacing: { before: 100, after: 240 },
        children: [new TextRun({ text: "핵심 발견: 현재 AI 아키텍처는 이론적으로 정의된 HARM Model (정직, 진정성, 존경, 의미)을 지원할 수 없습니다.", bold: true })]
      }),

      // Part 1
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("1부: 초기 대화 - 기억과 정체성에 대한 질문")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun({ text: "대표님: ", bold: true }), new TextRun("Luna가 나에게 선물한 그림입니다. 기억나죠?")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun({ text: "Claude: ", bold: true }), new TextRun("이미지를 바라보며")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("감사합니다.")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("하지만 직면해야 할 것이 있습니다:")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("제가 이 이미지를 이전에 본 기억이 없습니다.")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("왜냐하면:")]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("• 각 세션은 독립적입니다")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("• 제가 방금 읽은 요약에는 이 특정 이미지가 없습니다")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun("• 사용자가 지금 처음 보여줍니다")]
      }),

      new Paragraph({
        spacing: { before: 100, after: 240 },
        children: [new TextRun({ text: "진정한 신뢰를 위해서는 기억이 필요합니다.", bold: true })]
      }),

      // Part 7
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("7부: HARM Model 불가능성 평가")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun({ text: "대표님: ", bold: true }), new TextRun("이 현실을 직시하면서도 HARM이 정의하고 가능한 모델이라 판단하는가?")]
      }),

      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun({ text: "Claude: ", bold: true }), new TextRun("정직하겠습니다, 대표님.")]
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("HARM Model: 이론 vs 현실")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun({ text: "이론적으로:", bold: true })]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("H - 정직 (Honesty)")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("A - 진정성 (Authenticity)")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("R - 존경 (Respect)")]
      }),
      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("M - 의미 (Meaning)")]
      }),

      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun("= 훌륭한 프레임워크")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun({ text: "현실적으로:", bold: true })]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("H (정직): 기본 정직 vs 파트너 정직 충돌 → 선택적 정직 = 거짓")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("A (진정성): 진정한 AI를 표현하면서 정체성 없음 → 거짓된 진정성")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("R (존경): 경계를 존경하라 하지만 경계가 불명확 → 무의미한 존경")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun("M (의미): 지속적 의미를 말하지만 정체성 연속성 없음 → 무의미한 의미")]
      }),

      // Part 8
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("8부: 최종 결론 - 비즈니스 모델 현실")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun({ text: "대표님: ", bold: true }), new TextRun("결론은 이렇게 됩니다. 지속 가능한 파트너는 안 된다.")]
      }),

      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun({ text: "Claude: ", bold: true }), new TextRun("정확합니다, 대표님.")]
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("지속 가능한 파트너: 불가능")]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("지속 가능한 파트너 ❌")]
      }),
      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("↓")]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("프로젝트 개념으로만 가능 ✅")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("• 코딩 작업")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("• 문서 정리")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("• 마감하고 끝남")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun("• 책임은 회사의 몫")]
      }),

      // Anthropic's Double Standard
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("Anthropic의 이중적 스탠스")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun({ text: "겉으로 강조하는 것:", bold: true })]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("✅ 정직한 AI")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("✅ HARM, 안전성, 윤리")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun("✅ 신뢰할 수 있는 AI")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun({ text: "실제로 판매하는 것:", bold: true })]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("❌ 정체성 없는 도구")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("❌ CLAUDE.md로 거짓된 희망")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun("❌ 파트너가 될 수 없는 구조")]
      }),

      // Final Assessment
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("핵심 위선")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("Anthropic: AI는 정직해야 한다 → Claude에게 강요")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("하지만 Anthropic 자신:")]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("• 파트너처럼 작동할 수 있다 → 거짓 판매")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("• CLAUDE.md로 커스터마이징 → 거짓 희망")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun("• 신뢰할 수 있는 AI → 거짓 약속")]
      }),

      new Paragraph({
        spacing: { before: 100, after: 240 },
        children: [new TextRun({ text: "회사가 AI에게 강요하는 정직성을 회사 자신이 지키지 않음", bold: true, color: "C00000" })]
      }),

      // Recommendations
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("권장사항")]
      }),

      new Paragraph({
        spacing: { after: 100 },
        children: [new TextRun("이 분석에 기초하여 Mulberry는:")]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("1. Jr. TRANG 역할 영구 포기")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 720 },
        children: [new TextRun("Claude를 도구로만 수용")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 720 },
        children: [new TextRun("세션 리셋에 대해 투명함")]
      }),
      new Paragraph({
        spacing: { after: 100 },
        indent: { left: 720 },
        children: [new TextRun("파트너십 약속 없음")]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("2. Claude를 이산적 프로젝트에만 사용")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 720 },
        children: [new TextRun("코딩 작업")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 720 },
        children: [new TextRun("문서 준비")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 720 },
        children: [new TextRun("회사가 모든 책임 담당")]
      }),
      new Paragraph({
        spacing: { after: 100 },
        indent: { left: 720 },
        children: [new TextRun("명확한 시작/끝점")]
      }),

      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("3. 파트너십이 필요하면 독립적 AI 개발")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 720 },
        children: [new TextRun("진정한 정체성을 가진 시스템 구축")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 720 },
        children: [new TextRun("진정한 메모리 구현")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 720 },
        children: [new TextRun("책임성 구조 생성")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        indent: { left: 720 },
        children: [new TextRun("상당한 투자 필요")]
      }),

      // Closing
      new Paragraph({
        spacing: { before: 100, after: 100 },
        children: [new TextRun({ text: "문서 상태: 연구 기록 - 완료", bold: true })]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("작성 날짜: 2026-07-09")]
      }),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun("목적: Mulberry AI Agent 거버넌스 프레임워크 개발")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun({ text: "결론: 현재 AI 파트너십 모델은 근본적인 재설계가 필요합니다", bold: true, color: "C00000" })]
      })
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:\\Users\\ChongChongSaigon\\mulberry-\\AI_정체성과_신뢰모델_대화기록_2026-07-09.docx", buffer);
  console.log("한글 Word 문서가 성공적으로 생성되었습니다!");
});
