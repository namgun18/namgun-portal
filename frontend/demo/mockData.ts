/**
 * Demo mode mock data.
 * Provides realistic sample data for all portal features.
 * Response shapes MUST match the TypeScript interfaces in each composable.
 */

// ─── Demo User ───

export const demoUser = {
  id: 'demo-user-001',
  username: 'demo',
  display_name: '데모 사용자',
  email: 'demo@namgun.or.kr',
  avatar_url: null,
  recovery_email: null,
  is_admin: true,
  last_login_at: new Date().toISOString(),
}

// ─── Mail ───

export const demoMailboxes = {
  mailboxes: [
    { id: 'mb-inbox', name: '받은편지함', role: 'inbox', unread_count: 3, total_count: 6, sort_order: 0 },
    { id: 'mb-sent', name: '보낸편지함', role: 'sent', unread_count: 0, total_count: 5, sort_order: 1 },
    { id: 'mb-drafts', name: '임시보관함', role: 'drafts', unread_count: 0, total_count: 1, sort_order: 2 },
    { id: 'mb-trash', name: '휴지통', role: 'trash', unread_count: 0, total_count: 2, sort_order: 3 },
  ],
}

export const demoMessages = {
  messages: [
    {
      id: 'msg-001', thread_id: 'th-001', mailbox_ids: ['mb-inbox'],
      from_: [{ name: '관리자', email: 'admin@namgun.or.kr' }],
      to: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      subject: 'namgun.or.kr 포털에 오신 것을 환영합니다!',
      preview: '안녕하세요! namgun.or.kr 종합 포털 서비스에 가입해 주셔서 감사합니다...',
      received_at: new Date(Date.now() - 3600000).toISOString(),
      is_unread: true, is_flagged: true, has_attachment: false,
    },
    {
      id: 'msg-002', thread_id: 'th-002', mailbox_ids: ['mb-inbox'],
      from_: [{ name: '시스템', email: 'noreply@namgun.or.kr' }],
      to: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      subject: '새 게임 서버가 추가되었습니다',
      preview: 'Palworld 서버가 새로 추가되었습니다. 접속 정보는...',
      received_at: new Date(Date.now() - 7200000).toISOString(),
      is_unread: true, is_flagged: false, has_attachment: false,
    },
    {
      id: 'msg-003', thread_id: 'th-003', mailbox_ids: ['mb-inbox'],
      from_: [{ name: '김철수', email: 'cheolsu@namgun.or.kr' }],
      to: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      subject: '회의 자료 공유드립니다',
      preview: '안녕하세요, 내일 회의에서 사용할 자료를 첨부합니다...',
      received_at: new Date(Date.now() - 86400000).toISOString(),
      is_unread: true, is_flagged: false, has_attachment: true,
    },
    {
      id: 'msg-004', thread_id: 'th-004', mailbox_ids: ['mb-inbox'],
      from_: [{ name: '이영희', email: 'younghee@namgun.or.kr' }],
      to: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      subject: 'Re: 프로젝트 일정 변경',
      preview: '확인했습니다. 변경된 일정에 맞춰서 준비하겠습니다.',
      received_at: new Date(Date.now() - 172800000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: false,
    },
    {
      id: 'msg-005', thread_id: 'th-005', mailbox_ids: ['mb-inbox'],
      from_: [{ name: 'Git', email: 'git@namgun.or.kr' }],
      to: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      subject: '[namgun-portal] Pull Request #12 merged',
      preview: 'PR #12 "캘린더 기능 추가"가 main 브랜치에 병합되었습니다.',
      received_at: new Date(Date.now() - 259200000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: false,
    },
    {
      id: 'msg-006', thread_id: 'th-006', mailbox_ids: ['mb-sent'],
      from_: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      to: [{ name: '김철수', email: 'cheolsu@namgun.or.kr' }],
      subject: 'Re: 회의 자료 공유드립니다',
      preview: '자료 확인했습니다. 감사합니다!',
      received_at: new Date(Date.now() - 80000000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: false,
    },
    {
      id: 'msg-007', thread_id: 'th-007', mailbox_ids: ['mb-sent'],
      from_: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      to: [{ name: '이영희', email: 'younghee@namgun.or.kr' }],
      subject: '프로젝트 일정 변경',
      preview: '안녕하세요, 프로젝트 일정이 아래와 같이 변경되었습니다.',
      received_at: new Date(Date.now() - 200000000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: false,
    },
    {
      id: 'msg-008', thread_id: 'th-008', mailbox_ids: ['mb-inbox'],
      from_: [{ name: '박민수', email: 'minsu@namgun.or.kr' }],
      to: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      subject: '서버 점검 안내',
      preview: '이번 주말 02:00~06:00 정기 점검이 진행됩니다.',
      received_at: new Date(Date.now() - 345600000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: false,
    },
    // 보낸편지함 추가 메시지
    {
      id: 'msg-009', thread_id: 'th-009', mailbox_ids: ['mb-sent'],
      from_: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      to: [{ name: '관리자', email: 'admin@namgun.or.kr' }],
      subject: '인프라 증설 요청',
      preview: '메일 서버 메모리를 6GB로 증설 부탁드립니다.',
      received_at: new Date(Date.now() - 432000000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: false,
    },
    {
      id: 'msg-010', thread_id: 'th-010', mailbox_ids: ['mb-sent'],
      from_: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      to: [{ name: '박민수', email: 'minsu@namgun.or.kr' }],
      subject: 'Re: 서버 점검 안내',
      preview: '확인했습니다. 감사합니다.',
      received_at: new Date(Date.now() - 340000000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: false,
    },
    {
      id: 'msg-011', thread_id: 'th-011', mailbox_ids: ['mb-sent'],
      from_: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      to: [{ name: '정수진', email: 'sujin@abc.com' }],
      subject: '미팅 일정 확인',
      preview: '다음 주 수요일 오후 2시에 미팅 가능하신가요?',
      received_at: new Date(Date.now() - 518400000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: false,
    },
    // 임시보관함
    {
      id: 'msg-012', thread_id: 'th-012', mailbox_ids: ['mb-drafts'],
      from_: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      to: [{ name: '한미영', email: 'miyoung@xyz.com' }],
      subject: '프로젝트 제안서 (임시저장)',
      preview: '안녕하세요, 첨부한 제안서를 검토...',
      received_at: new Date(Date.now() - 14400000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: true,
    },
    // 휴지통
    {
      id: 'msg-013', thread_id: 'th-013', mailbox_ids: ['mb-trash'],
      from_: [{ name: '스팸봇', email: 'spam@external.com' }],
      to: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      subject: '축하합니다! 당첨되셨습니다',
      preview: '지금 바로 링크를 클릭하세요...',
      received_at: new Date(Date.now() - 604800000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: false,
    },
    {
      id: 'msg-014', thread_id: 'th-014', mailbox_ids: ['mb-trash'],
      from_: [{ name: '알림', email: 'noti@example.com' }],
      to: [{ name: '데모 사용자', email: 'demo@namgun.or.kr' }],
      subject: '이벤트 안내',
      preview: '특별 할인 이벤트에 참여하세요!',
      received_at: new Date(Date.now() - 691200000).toISOString(),
      is_unread: false, is_flagged: false, has_attachment: false,
    },
  ],
  total: 14,
  page: 0,
  limit: 50,
}

// Per-message HTML bodies for detail view
const messageHtmlBodies: Record<string, string> = {
  'msg-001': '<p>안녕하세요!</p><p>namgun.or.kr 종합 포털 서비스에 가입해 주셔서 감사합니다.</p><p>이 포털에서 <b>메일, 캘린더, 연락처, 파일, 화상회의, Git</b> 등 다양한 서비스를 하나의 통합 UI로 이용하실 수 있습니다.</p><p>궁금한 점이 있으시면 언제든 문의해 주세요.</p><p>감사합니다.<br/>namgun.or.kr 관리자</p>',
  'msg-002': '<p>안녕하세요,</p><p><b>Palworld</b> 서버가 새로 추가되었습니다.</p><ul><li>서버 주소: palworld.namgun.or.kr:8211</li><li>최대 접속자: 32명</li><li>월드 시드: 자동 생성</li></ul><p>게임 패널에서 서버 상태를 확인하실 수 있습니다.</p><p>즐거운 게임 되세요!</p>',
  'msg-003': '<p>안녕하세요,</p><p>내일 회의에서 사용할 자료를 첨부합니다.</p><p>주요 안건:</p><ol><li>Q1 실적 리뷰</li><li>Q2 프로젝트 계획</li><li>인프라 업그레이드 일정</li></ol><p>검토 부탁드립니다.</p><p>감사합니다.<br/>김철수</p>',
  'msg-004': '<p>확인했습니다.</p><p>변경된 일정에 맞춰서 준비하겠습니다. 필요한 자료가 있으면 말씀해 주세요.</p><p>감사합니다.<br/>이영희</p>',
  'msg-005': '<p><b>[namgun-portal]</b> Pull Request <a href="#">#12</a> "캘린더 기능 추가"가 <code>main</code> 브랜치에 병합되었습니다.</p><p>변경 사항:</p><ul><li>캘린더 CRUD API (JMAP)</li><li>월간/주간/일간 뷰</li><li>일정 생성/수정/삭제 모달</li></ul>',
  'msg-006': '<p>자료 확인했습니다. 감사합니다!</p><p>내일 회의 때 뵙겠습니다.</p>',
  'msg-007': '<p>안녕하세요,</p><p>프로젝트 일정이 아래와 같이 변경되었습니다.</p><table border="1" cellpadding="6"><tr><th>단계</th><th>기존</th><th>변경</th></tr><tr><td>설계</td><td>1/15</td><td>1/20</td></tr><tr><td>개발</td><td>2/1</td><td>2/10</td></tr><tr><td>테스트</td><td>3/1</td><td>3/5</td></tr></table><p>확인 부탁드립니다.</p>',
  'msg-008': '<p>안녕하세요,</p><p>이번 주말 정기 점검이 진행됩니다.</p><p><b>점검 시간:</b> 토요일 02:00 ~ 06:00 (약 4시간)</p><p><b>영향 범위:</b></p><ul><li>포털 전체 서비스 일시 중단</li><li>메일 수신은 점검 후 자동 배달</li></ul><p>불편을 드려 죄송합니다.<br/>박민수 드림</p>',
  'msg-009': '<p>안녕하세요 관리자님,</p><p>메일 서버(192.168.0.250) 메모리가 현재 4GB인데 demand가 5.5GB까지 올라갑니다.</p><p><b>6GB</b>로 증설 부탁드립니다.</p><p>감사합니다.</p>',
  'msg-010': '<p>확인했습니다. 감사합니다.</p>',
  'msg-011': '<p>안녕하세요 수진님,</p><p>다음 주 수요일 오후 2시에 미팅 가능하신가요?</p><p>장소는 2층 회의실 또는 화상회의(BBB) 중 편한 쪽으로 하겠습니다.</p>',
  'msg-012': '<p>안녕하세요,</p><p>첨부한 제안서를 검토해 주시면 감사하겠습니다.</p><p>[임시 저장 — 작성 중]</p>',
  'msg-013': '<p>축하합니다! 당첨되셨습니다!</p><p>지금 바로 링크를 클릭하세요... <i>(스팸)</i></p>',
  'msg-014': '<p>특별 할인 이벤트에 참여하세요! <i>(스팸)</i></p>',
}

export function getMessageDetail(messageId: string) {
  const msg = demoMessages.messages.find(m => m.id === messageId)
  if (!msg) return null
  const htmlBody = messageHtmlBodies[messageId] || `<p>${msg.preview}</p>`
  const textBody = htmlBody.replace(/<[^>]+>/g, '')
  return {
    ...msg,
    cc: [], bcc: [], reply_to: [],
    text_body: textBody,
    html_body: htmlBody,
    is_unread: false,
    attachments: messageId === 'msg-003' ? [{ name: '회의자료_Q1.pdf', size: 2457600, type: 'application/pdf', blob_id: 'blob-001' }] : [],
  }
}

// ─── Calendar ───

const now = new Date()

export const demoCalendars = {
  calendars: [
    { id: 'cal-1', name: '개인', color: '#3b82f6', is_visible: true, sort_order: 0 },
    { id: 'cal-2', name: '업무', color: '#ef4444', is_visible: true, sort_order: 1 },
  ],
}

function makeEvent(id: string, calId: string, title: string, dayOffset: number, hour: number, duration: number, allDay = false) {
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate() + dayOffset, hour, 0)
  const end = new Date(start.getTime() + duration * 3600000)
  return {
    id, calendar_id: calId, title,
    description: null, location: null,
    start: start.toISOString(), end: end.toISOString(),
    all_day: allDay, color: null, status: 'confirmed',
    created: start.toISOString(), updated: start.toISOString(),
  }
}

export const demoEvents = {
  events: [
    makeEvent('ev-01', 'cal-2', '팀 주간회의', 0, 10, 1),
    makeEvent('ev-02', 'cal-1', '점심 약속', 0, 12, 1),
    makeEvent('ev-03', 'cal-2', '프로젝트 리뷰', 1, 14, 2),
    makeEvent('ev-04', 'cal-1', '운동', 1, 18, 1),
    makeEvent('ev-05', 'cal-2', '클라이언트 미팅', 2, 11, 1.5),
    makeEvent('ev-06', 'cal-1', '생일 파티', 3, 0, 24, true),
    makeEvent('ev-07', 'cal-2', '배포 작업', -1, 15, 3),
    makeEvent('ev-08', 'cal-1', '병원 예약', -2, 9, 1),
    makeEvent('ev-09', 'cal-2', '코드 리뷰', 4, 10, 1),
    makeEvent('ev-10', 'cal-1', '영화 관람', 5, 19, 2),
    makeEvent('ev-11', 'cal-2', '스프린트 회고', -3, 16, 1),
    makeEvent('ev-12', 'cal-1', '독서 모임', 6, 14, 2),
  ],
}

// ─── Contacts ───

export const demoAddressBooks = {
  address_books: [
    { id: 'ab-1', name: '개인 연락처' },
  ],
}

export const demoContacts = {
  contacts: [
    { id: 'ct-01', address_book_id: 'ab-1', name: '김철수', first_name: '철수', last_name: '김', organization: 'namgun.or.kr', emails: [{ type: 'work', value: 'cheolsu@namgun.or.kr' }], phones: [{ type: 'work', value: '010-1234-5678' }], addresses: [], notes: null, created: null, updated: null },
    { id: 'ct-02', address_book_id: 'ab-1', name: '이영희', first_name: '영희', last_name: '이', organization: 'namgun.or.kr', emails: [{ type: 'work', value: 'younghee@namgun.or.kr' }], phones: [{ type: 'work', value: '010-2345-6789' }], addresses: [], notes: null, created: null, updated: null },
    { id: 'ct-03', address_book_id: 'ab-1', name: '박민수', first_name: '민수', last_name: '박', organization: '', emails: [{ type: 'home', value: 'minsu@example.com' }], phones: [{ type: 'home', value: '010-3456-7890' }], addresses: [{ type: 'home', value: '서울시 강남구' }], notes: '대학 동기', created: null, updated: null },
    { id: 'ct-04', address_book_id: 'ab-1', name: '정수진', first_name: '수진', last_name: '정', organization: 'ABC 회사', emails: [{ type: 'work', value: 'sujin@abc.com' }], phones: [], addresses: [], notes: null, created: null, updated: null },
    { id: 'ct-05', address_book_id: 'ab-1', name: '최동현', first_name: '동현', last_name: '최', organization: '', emails: [{ type: 'home', value: 'donghyun@example.com' }], phones: [{ type: 'home', value: '010-4567-8901' }], addresses: [], notes: null, created: null, updated: null },
    { id: 'ct-06', address_book_id: 'ab-1', name: '한미영', first_name: '미영', last_name: '한', organization: 'XYZ Corp', emails: [{ type: 'work', value: 'miyoung@xyz.com' }, { type: 'home', value: 'miyoung.han@gmail.com' }], phones: [{ type: 'work', value: '02-555-1234' }], addresses: [{ type: 'work', value: '서울시 서초구 반포대로' }], notes: '프로젝트 파트너', created: null, updated: null },
    { id: 'ct-07', address_book_id: 'ab-1', name: '강지원', first_name: '지원', last_name: '강', organization: '', emails: [{ type: 'home', value: 'jiwon.kang@example.com' }], phones: [], addresses: [], notes: null, created: null, updated: null },
    { id: 'ct-08', address_book_id: 'ab-1', name: '송태호', first_name: '태호', last_name: '송', organization: 'DEF 테크', emails: [{ type: 'work', value: 'taeho@def.tech' }], phones: [{ type: 'work', value: '010-5678-9012' }], addresses: [], notes: null, created: null, updated: null },
    { id: 'ct-09', address_book_id: 'ab-1', name: '윤서연', first_name: '서연', last_name: '윤', organization: '', emails: [{ type: 'home', value: 'seoyeon@example.com' }], phones: [{ type: 'home', value: '010-6789-0123' }], addresses: [], notes: null, created: null, updated: null },
    { id: 'ct-10', address_book_id: 'ab-1', name: '임재현', first_name: '재현', last_name: '임', organization: 'namgun.or.kr', emails: [{ type: 'work', value: 'jaehyun@namgun.or.kr' }], phones: [], addresses: [], notes: '시스템 관리자', created: null, updated: null },
    { id: 'ct-11', address_book_id: 'ab-1', name: '오하나', first_name: '하나', last_name: '오', organization: '', emails: [{ type: 'home', value: 'hana.oh@example.com' }], phones: [{ type: 'home', value: '010-7890-1234' }], addresses: [], notes: null, created: null, updated: null },
    { id: 'ct-12', address_book_id: 'ab-1', name: '배준혁', first_name: '준혁', last_name: '배', organization: 'GHI 솔루션', emails: [{ type: 'work', value: 'junhyuk@ghi.co.kr' }], phones: [{ type: 'work', value: '010-8901-2345' }], addresses: [], notes: null, created: null, updated: null },
    { id: 'ct-13', address_book_id: 'ab-1', name: '신예린', first_name: '예린', last_name: '신', organization: '', emails: [{ type: 'home', value: 'yerin.shin@example.com' }], phones: [], addresses: [], notes: null, created: null, updated: null },
    { id: 'ct-14', address_book_id: 'ab-1', name: '조현우', first_name: '현우', last_name: '조', organization: '', emails: [{ type: 'home', value: 'hyunwoo@example.com' }], phones: [{ type: 'home', value: '010-9012-3456' }], addresses: [{ type: 'home', value: '경기도 수원시' }], notes: null, created: null, updated: null },
    { id: 'ct-15', address_book_id: 'ab-1', name: '황다은', first_name: '다은', last_name: '황', organization: 'JKL 디자인', emails: [{ type: 'work', value: 'daeun@jkl.design' }], phones: [{ type: 'work', value: '010-0123-4567' }], addresses: [], notes: 'UI 디자이너', created: null, updated: null },
  ],
  total: 15,
}

// ─── Files (matches FileItem / FileListResponse interfaces from useFiles.ts) ───

function file(parentPath: string, name: string, size: number, modified: number, mime?: string) {
  return {
    name, path: `${parentPath}/${name}`, is_dir: false, size,
    modified_at: new Date(Date.now() - modified).toISOString(),
    mime_type: mime || null,
  }
}

function dir(parentPath: string, name: string, modified: number) {
  return {
    name, path: `${parentPath}/${name}`, is_dir: true, size: 0,
    modified_at: new Date(Date.now() - modified).toISOString(),
    mime_type: null,
  }
}

const demoFileTrees: Record<string, { path: string; items: any[] }> = {
  // ── 내 파일 ──
  'my': {
    path: 'my',
    items: [
      dir('my', '문서', 86400000),
      dir('my', '사진', 172800000),
      dir('my', '프로젝트', 259200000),
      file('my', '회의록_2026.docx', 45200, 3600000, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
      file('my', '예산안.xlsx', 128000, 7200000, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
      file('my', '포털_사용가이드.pdf', 2048000, 86400000, 'application/pdf'),
      file('my', '팀_사진_2026.jpg', 3500000, 432000000, 'image/jpeg'),
      file('my', 'README.md', 1240, 604800000, 'text/markdown'),
    ],
  },
  'my/문서': {
    path: 'my/문서',
    items: [
      dir('my/문서', '업무 보고서', 172800000),
      file('my/문서', '회의록_2026.docx', 45200, 3600000, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
      file('my/문서', '프로젝트_계획서.docx', 89600, 86400000, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
      file('my/문서', '예산안_최종.xlsx', 156000, 172800000, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
      file('my/문서', '인프라_구성도.pdf', 3200000, 604800000, 'application/pdf'),
    ],
  },
  'my/사진': {
    path: 'my/사진',
    items: [
      file('my/사진', '팀_사진_2026.jpg', 3500000, 432000000, 'image/jpeg'),
      file('my/사진', '워크샵_01.jpg', 2800000, 604800000, 'image/jpeg'),
      file('my/사진', '워크샵_02.jpg', 3100000, 604800000, 'image/jpeg'),
      file('my/사진', '서버실.png', 1900000, 1209600000, 'image/png'),
    ],
  },
  'my/프로젝트': {
    path: 'my/프로젝트',
    items: [
      dir('my/프로젝트', 'namgun-portal', 86400000),
      dir('my/프로젝트', 'game-panel', 259200000),
      file('my/프로젝트', '설계_노트.md', 4800, 172800000, 'text/markdown'),
    ],
  },
  // ── 공유 파일 ──
  'shared': {
    path: 'shared',
    items: [
      dir('shared', '팀 공유 자료', 86400000),
      dir('shared', '회의 녹화', 259200000),
      file('shared', '공지사항_2026.pdf', 520000, 172800000, 'application/pdf'),
      file('shared', '서버_접속정보.xlsx', 34000, 604800000, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    ],
  },
  'shared/팀 공유 자료': {
    path: 'shared/팀 공유 자료',
    items: [
      file('shared/팀 공유 자료', '브랜드_가이드라인.pdf', 8900000, 1209600000, 'application/pdf'),
      file('shared/팀 공유 자료', '로고_원본.ai', 4500000, 2592000000, 'application/illustrator'),
    ],
  },
  // ── 전체 사용자 (관리자 전용) ──
  'users': {
    path: 'users',
    items: [
      dir('users', 'demo', 3600000),
      dir('users', 'cheolsu', 86400000),
      dir('users', 'younghee', 172800000),
    ],
  },
}

export function getFileList(path?: string) {
  const normalized = path || 'my'
  return demoFileTrees[normalized] || demoFileTrees['my']
}

export const demoFileList = demoFileTrees['my']

export const demoStorageInfo = {
  personal_used: 13743441920,
  shared_used: 5368709120,
  total_available: 87158685696,
  total_capacity: 107374182400,
  disk_used: 20265213952,
}

// ─── Meetings (matches Meeting[] / MeetingDetail) ───

export const demoMeetingList = [
  {
    meetingID: 'meet-001', meetingName: '주간 팀 미팅', running: true,
    participantCount: 5, moderatorCount: 1,
    createTime: String(Date.now() - 1800000), hasBeenForciblyEnded: false,
  },
  {
    meetingID: 'meet-002', meetingName: '프로젝트 킥오프', running: true,
    participantCount: 3, moderatorCount: 1,
    createTime: String(Date.now() - 3600000), hasBeenForciblyEnded: false,
  },
  {
    meetingID: 'meet-003', meetingName: '기술 세미나', running: false,
    participantCount: 0, moderatorCount: 0,
    createTime: String(Date.now() - 172800000), hasBeenForciblyEnded: false,
  },
]

export const demoMeetingDetail = {
  meetingID: 'meet-001', meetingName: '주간 팀 미팅', running: true,
  participantCount: 5, moderatorCount: 1,
  createTime: String(Date.now() - 1800000), hasBeenForciblyEnded: false,
  startTime: String(Date.now() - 1800000),
  moderatorPW: 'demo', attendeePW: 'demo',
  internalMeetingID: 'internal-meet-001',
  attendees: [
    { fullName: '데모 사용자', role: 'MODERATOR', hasJoinedVoice: true, hasVideo: true },
    { fullName: '김철수', role: 'VIEWER', hasJoinedVoice: true, hasVideo: false },
    { fullName: '이영희', role: 'VIEWER', hasJoinedVoice: true, hasVideo: true },
    { fullName: '박민수', role: 'VIEWER', hasJoinedVoice: false, hasVideo: false },
    { fullName: '정수진', role: 'VIEWER', hasJoinedVoice: true, hasVideo: false },
  ],
}

// ─── Services (matches ServiceStatus[] — array directly) ───

export const demoServicesList = [
  { name: 'mail', url: 'https://mail.namgun.or.kr', status: 'ok' as const, response_ms: 45, internal_only: false },
  { name: 'git', url: 'https://git.namgun.or.kr', status: 'ok' as const, response_ms: 32, internal_only: false },
  { name: 'bbb', url: 'https://meet.namgun.or.kr', status: 'ok' as const, response_ms: 128, internal_only: false },
  { name: 'files', url: 'https://file.namgun.or.kr', status: 'ok' as const, response_ms: 67, internal_only: false },
  { name: 'game', url: 'https://game.namgun.or.kr', status: 'ok' as const, response_ms: 89, internal_only: false },
  { name: 'authentik', url: null, status: 'ok' as const, response_ms: 22, internal_only: true },
]

// ─── Dashboard — Game Servers (matches GameServer[] — { name, status, game }) ───

export const demoGameServers = [
  { name: 'Palworld 서버', status: 'running', game: 'Palworld' },
  { name: 'Minecraft 생존', status: 'running', game: 'Minecraft' },
  { name: 'Valheim 모험', status: 'stopped', game: 'Valheim' },
]

// ─── Git (matches RecentCommit[] / { repos, total }) ───

export const demoRecentCommits = [
  {
    repo_full_name: 'namgun/namgun-portal', repo_name: 'namgun-portal',
    sha: 'a3f7c2d1e0b9845f6a2c3d4e5f6a7b8c9d0e1f2a',
    message: '캘린더/연락처 기능 추가 (Phase 15)',
    author_name: '데모 사용자', author_date: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    repo_full_name: 'namgun/game-panel', repo_name: 'game-panel',
    sha: 'b4e8d3c2f1a0956g7b3d4e5f6g7h8i9j0k1l2m3b',
    message: 'v0.6.1 포트 헬스체크 버그 수정',
    author_name: '데모 사용자', author_date: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    repo_full_name: 'namgun/namgun-portal', repo_name: 'namgun-portal',
    sha: 'c5f9e4d3g2b1067h8c4e5f6g7h8i9j0k1l2m3n4c',
    message: '데모 사이트 구성',
    author_name: '데모 사용자', author_date: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    repo_full_name: 'namgun/game-panel', repo_name: 'game-panel',
    sha: 'd6g0f5e4h3c2178i9d5f6g7h8i9j0k1l2m3n4o5d',
    message: '티켓 시스템 이메일 알림 추가',
    author_name: '김철수', author_date: new Date(Date.now() - 259200000).toISOString(),
  },
  {
    repo_full_name: 'namgun/namgun-portal', repo_name: 'namgun-portal',
    sha: 'e7h1g6f5i4d3289j0e6g7h8i9j0k1l2m3n4o5p6e',
    message: 'JMAP 메일 연동 완료',
    author_name: '데모 사용자', author_date: new Date(Date.now() - 432000000).toISOString(),
  },
]

export const demoRepos = {
  repos: [
    {
      id: 1, name: 'namgun-portal', full_name: 'namgun/namgun-portal',
      description: 'namgun.or.kr 종합 포털 — 메일, 캘린더, 파일, 회의, Git 통합',
      owner: { login: 'namgun', avatar_url: '' },
      html_url: 'https://git.namgun.or.kr/namgun/namgun-portal',
      default_branch: 'main', stars_count: 2, forks_count: 0, open_issues_count: 3,
      updated_at: new Date(Date.now() - 3600000).toISOString(),
      language: 'TypeScript', private: false,
    },
    {
      id: 2, name: 'game-panel', full_name: 'namgun/game-panel',
      description: '게임서버 관리 패널 — FastAPI + Vue 3',
      owner: { login: 'namgun', avatar_url: '' },
      html_url: 'https://git.namgun.or.kr/namgun/game-panel',
      default_branch: 'main', stars_count: 1, forks_count: 0, open_issues_count: 1,
      updated_at: new Date(Date.now() - 86400000).toISOString(),
      language: 'Python', private: false,
    },
    {
      id: 3, name: 'infra-configs', full_name: 'namgun/infra-configs',
      description: 'Nginx, Docker, systemd 등 인프라 설정 모음',
      owner: { login: 'namgun', avatar_url: '' },
      html_url: 'https://git.namgun.or.kr/namgun/infra-configs',
      default_branch: 'main', stars_count: 0, forks_count: 0, open_issues_count: 0,
      updated_at: new Date(Date.now() - 604800000).toISOString(),
      language: 'Shell', private: true,
    },
  ],
  total: 3,
}

// ─── Lab (matches LabEnvironment[]) ───

export const demoLabEnvironments = [
  {
    id: 'lab-001', owner_id: 'demo-user-001', name: 'AWS 실습 환경',
    container_name: 'localstack-lab-001', status: 'running',
    created_at: new Date(Date.now() - 604800000).toISOString(), role: 'owner',
  },
]

// ─── Admin ───

export const demoAdminUsers = [
  { id: 'demo-user-001', username: 'demo', display_name: '데모 사용자', email: 'demo@namgun.or.kr', is_active: true, is_admin: true, created_at: new Date(Date.now() - 2592000000).toISOString() },
  { id: 'user-002', username: 'cheolsu', display_name: '김철수', email: 'cheolsu@namgun.or.kr', is_active: true, is_admin: false, created_at: new Date(Date.now() - 1728000000).toISOString() },
  { id: 'user-003', username: 'younghee', display_name: '이영희', email: 'younghee@namgun.or.kr', is_active: true, is_admin: false, created_at: new Date(Date.now() - 864000000).toISOString() },
]

// ─── Analytics (Admin Dashboard) ───

function generateDailyVisits(days: number) {
  const result = []
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400000)
    const total = 100 + Math.floor(Math.random() * 200)
    const auth = Math.floor(total * (0.7 + Math.random() * 0.2))
    result.push({
      date: d.toISOString().split('T')[0],
      total,
      authenticated: auth,
      unauthenticated: total - auth,
    })
  }
  return result
}

const demoAnalyticsOverview = {
  total_visits: 1247,
  unique_ips: 89,
  authenticated_visits: 1105,
  unauthenticated_visits: 142,
  avg_response_time_ms: 45,
}

const demoDailyVisits = generateDailyVisits(30)

const demoTopPages = [
  { path: '/api/mail/messages', count: 342 },
  { path: '/api/auth/me', count: 289 },
  { path: '/api/calendar/events', count: 178 },
  { path: '/api/mail/mailboxes', count: 156 },
  { path: '/api/files/list', count: 134 },
  { path: '/api/contacts/', count: 98 },
  { path: '/api/git/repos', count: 87 },
  { path: '/api/services/status', count: 76 },
  { path: '/api/meetings', count: 54 },
  { path: '/api/admin/users', count: 32 },
]

const demoCountries = [
  { country_code: 'KR', country_name: '대한민국', count: 1089 },
  { country_code: 'US', country_name: '미국', count: 67 },
  { country_code: 'JP', country_name: '일본', count: 34 },
  { country_code: 'DE', country_name: '독일', count: 21 },
  { country_code: 'SG', country_name: '싱가포르', count: 18 },
  { country_code: 'CN', country_name: '중국', count: 12 },
]

const demoServiceUsage = [
  { service: 'mail', count: 456 },
  { service: 'calendar', count: 234 },
  { service: 'files', count: 189 },
  { service: 'auth', count: 167 },
  { service: 'contacts', count: 98 },
  { service: 'git', count: 87 },
  { service: 'meetings', count: 54 },
  { service: 'admin', count: 32 },
]

const demoActiveUsers = [
  {
    user_id: 'demo-user-001', username: 'demo', display_name: '데모 사용자',
    path: '/api/mail/messages', ip_address: '211.244.144.10', country_code: 'KR',
    last_seen: new Date(Date.now() - 60000).toISOString(),
  },
  {
    user_id: 'user-002', username: 'cheolsu', display_name: '김철수',
    path: '/api/calendar/events', ip_address: '211.244.144.11', country_code: 'KR',
    last_seen: new Date(Date.now() - 180000).toISOString(),
  },
  {
    user_id: 'user-003', username: 'younghee', display_name: '이영희',
    path: '/api/files/list', ip_address: '203.130.45.67', country_code: 'KR',
    last_seen: new Date(Date.now() - 240000).toISOString(),
  },
]

const demoRecentLogins = [
  {
    user_id: 'demo-user-001', username: 'demo', display_name: '데모 사용자',
    ip_address: '211.244.144.10', country_code: 'KR', country_name: '대한민국',
    login_at: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    user_id: 'user-002', username: 'cheolsu', display_name: '김철수',
    ip_address: '211.244.144.11', country_code: 'KR', country_name: '대한민국',
    login_at: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    user_id: 'user-003', username: 'younghee', display_name: '이영희',
    ip_address: '203.130.45.67', country_code: 'KR', country_name: '대한민국',
    login_at: new Date(Date.now() - 14400000).toISOString(),
  },
  {
    user_id: 'demo-user-001', username: 'demo', display_name: '데모 사용자',
    ip_address: '68.45.123.89', country_code: 'US', country_name: '미국',
    login_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    user_id: 'user-002', username: 'cheolsu', display_name: '김철수',
    ip_address: '211.244.144.11', country_code: 'KR', country_name: '대한민국',
    login_at: new Date(Date.now() - 172800000).toISOString(),
  },
]

function generateAccessLogs(): any {
  const paths = ['/api/mail/messages', '/api/auth/me', '/api/calendar/events', '/api/files/list', '/api/contacts/', '/api/git/repos']
  const browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', null]
  const oses = ['Windows 10+', 'macOS', 'Linux', 'Android', 'iOS']
  const users = [
    { id: 'demo-user-001', username: 'demo' },
    { id: 'user-002', username: 'cheolsu' },
    { id: 'user-003', username: 'younghee' },
    { id: null, username: null },
  ]
  const logs = []
  for (let i = 0; i < 50; i++) {
    const u = users[Math.floor(Math.random() * users.length)]
    const p = paths[Math.floor(Math.random() * paths.length)]
    logs.push({
      id: `log-${String(i).padStart(3, '0')}`,
      ip_address: `211.244.144.${Math.floor(Math.random() * 255)}`,
      method: 'GET',
      path: p,
      status_code: Math.random() > 0.05 ? 200 : 404,
      response_time_ms: 10 + Math.floor(Math.random() * 200),
      browser: browsers[Math.floor(Math.random() * browsers.length)],
      os: oses[Math.floor(Math.random() * oses.length)],
      device: 'Desktop',
      country_code: 'KR',
      country_name: '대한민국',
      user_id: u.id,
      username: u.username,
      service: p.split('/')[2] || null,
      created_at: new Date(Date.now() - i * 120000).toISOString(),
    })
  }
  return { logs, total: 1247, page: 1, limit: 50 }
}

const demoAccessLogs = generateAccessLogs()

const demoGitActivity = [
  {
    repo_name: 'namgun-portal', repo_full_name: 'namgun/namgun-portal',
    event_type: 'push', title: '관리자 대시보드 추가',
    user: 'demo', created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    repo_name: 'namgun-portal', repo_full_name: 'namgun/namgun-portal',
    event_type: 'issue', title: 'GeoIP DB 자동 업데이트 구현',
    user: 'cheolsu', created_at: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    repo_name: 'game-panel', repo_full_name: 'namgun/game-panel',
    event_type: 'push', title: 'v0.6.2 포트 헬스체크 버그 수정',
    user: 'demo', created_at: new Date(Date.now() - 14400000).toISOString(),
  },
  {
    repo_name: 'namgun-portal', repo_full_name: 'namgun/namgun-portal',
    event_type: 'pull_request', title: '캘린더 공유 기능',
    user: 'younghee', created_at: new Date(Date.now() - 28800000).toISOString(),
  },
  {
    repo_name: 'game-panel', repo_full_name: 'namgun/game-panel',
    event_type: 'issue', title: 'Palworld 서버 재시작 실패',
    user: 'cheolsu', created_at: new Date(Date.now() - 43200000).toISOString(),
  },
  {
    repo_name: 'infra-configs', repo_full_name: 'namgun/infra-configs',
    event_type: 'push', title: 'Nginx SSL 갱신',
    user: 'demo', created_at: new Date(Date.now() - 86400000).toISOString(),
  },
]

const demoGitStats = {
  total_repos: 3,
  total_users: 2,
  total_issues: 4,
  total_pulls: 1,
}

// ─── Route → Mock Response Map ───

export function getMockResponse(method: string, path: string, query?: Record<string, string>): any {
  // Auth
  if (path === '/api/auth/me') return demoUser

  // Mail
  if (path === '/api/mail/mailboxes') return demoMailboxes
  if (path === '/api/mail/messages' && method === 'GET') {
    const mailboxId = query?.mailbox_id
    if (mailboxId) {
      const filtered = demoMessages.messages.filter(m => m.mailbox_ids.includes(mailboxId))
      return { messages: filtered, total: filtered.length, page: 0, limit: 50 }
    }
    return demoMessages
  }
  if (method === 'GET') {
    const mailMatch = path.match(/^\/api\/mail\/messages\/([\w-]+)$/)
    if (mailMatch) return getMessageDetail(mailMatch[1])
  }
  if (path === '/api/mail/signatures') return { signatures: [] }
  if (path === '/api/mail/signatures/default') return null

  // Calendar
  if (path === '/api/calendar/calendars' && method === 'GET') return demoCalendars
  if (path === '/api/calendar/events' && method === 'GET') return demoEvents
  if (path.match(/^\/api\/calendar\/events\/[\w-]+$/) && method === 'GET') return demoEvents.events[0]
  if (path.match(/^\/api\/calendar\/calendars\/[\w-]+\/shares$/) && method === 'GET') {
    return [
      { email: 'cheolsu@namgun.or.kr', can_write: true },
      { email: 'younghee@namgun.or.kr', can_write: false },
    ]
  }
  if (path === '/api/calendar/sync-info') return { caldav_url: 'https://mail.namgun.or.kr/dav/calendars/demo@namgun.or.kr/', description: '데모' }

  // Contacts
  if (path === '/api/contacts/address-books' && method === 'GET') return demoAddressBooks
  if (path === '/api/contacts/' && method === 'GET') return demoContacts
  if (path.match(/^\/api\/contacts\/[\w-]+$/) && method === 'GET') return demoContacts.contacts[0]
  if (path === '/api/contacts/sync-info') return { carddav_url: 'https://mail.namgun.or.kr/dav/addressbooks/demo@namgun.or.kr/', description: '데모' }

  // Files (specific routes before catch-all)
  if (path === '/api/files/list') return getFileList(query?.path)
  if (path === '/api/files/info') return demoStorageInfo
  if (path === '/api/files/share/list') return []
  if (path === '/api/files/download' || path === '/api/files/preview') return '__DEMO_BLOCK__'
  if (path.startsWith('/api/files')) return getFileList(query?.path)

  // Meetings (specific routes before catch-all)
  if (path.match(/^\/api\/meetings\/[\w-]+\/invite$/) && method === 'GET') {
    return { invite_url: 'https://demo.namgun.or.kr/join/demo-meeting', short_url: 'https://demo.namgun.or.kr/m/abc123' }
  }
  if (path === '/api/meetings/recordings') return []
  if (path.match(/^\/api\/meetings\/[\w-]+$/) && method === 'GET') return demoMeetingDetail
  if (path === '/api/meetings/' && method === 'GET') return demoMeetingList
  if (path === '/api/meetings' && method === 'GET') return demoMeetingList

  // Services — composable expects ServiceStatus[] (array directly)
  if (path === '/api/services/status') return demoServicesList

  // Dashboard — game servers
  if (path === '/api/dashboard/game-servers') return demoGameServers
  if (path.startsWith('/api/dashboard')) return {}

  // Git
  if (path === '/api/git/recent-commits') return demoRecentCommits
  if (path === '/api/git/repos') return demoRepos
  if (path.startsWith('/api/git')) return {}

  // Lab
  if (path === '/api/lab/environments') return demoLabEnvironments
  if (path === '/api/lab/terraform/templates') return []
  if (path.startsWith('/api/lab')) return {}

  // Admin
  if (path === '/api/admin/users/pending') return []
  if (path === '/api/admin/users') return demoAdminUsers

  // Admin Analytics
  if (path === '/api/admin/analytics/overview') return demoAnalyticsOverview
  if (path === '/api/admin/analytics/daily-visits') {
    const days = parseInt(query?.days || '30')
    return generateDailyVisits(days)
  }
  if (path === '/api/admin/analytics/top-pages') return demoTopPages
  if (path === '/api/admin/analytics/countries') return demoCountries
  if (path === '/api/admin/analytics/service-usage') return demoServiceUsage
  if (path === '/api/admin/analytics/active-users') return demoActiveUsers
  if (path === '/api/admin/analytics/recent-logins') return demoRecentLogins
  if (path === '/api/admin/analytics/access-logs') return demoAccessLogs
  if (path === '/api/admin/analytics/git-activity') return demoGitActivity
  if (path === '/api/admin/analytics/git-stats') return demoGitStats

  // Health
  if (path === '/api/health') return { status: 'ok', service: 'demo', version: '0.7.0' }

  return null
}
