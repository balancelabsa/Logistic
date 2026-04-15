export default function PlaybackControls({ playing, speed, index, total, currentTimestamp, onPlay, onPause, onReset, setSpeed }) {
  return (
    <div className="controls">
      <button onClick={onPlay} disabled={total === 0 || playing}>تشغيل</button>
      <button onClick={onPause} disabled={!playing}>إيقاف مؤقت</button>
      <button onClick={onReset}>إعادة</button>
      <button onClick={() => setSpeed(1)} className={speed === 1 ? 'active' : ''}>سرعة 1x</button>
      <button onClick={() => setSpeed(2)} className={speed === 2 ? 'active' : ''}>سرعة 2x</button>
      <button onClick={() => setSpeed(4)} className={speed === 4 ? 'active' : ''}>سرعة 4x</button>
      <span>النقطة الحالية: {total ? `${index + 1}/${total}` : '-'}</span>
      <span>وقت التشغيل: {currentTimestamp || '-'}</span>
    </div>
  )
}
