export default function ErrorState({ message, onRetry }) {
  return (
    <div className="state-box error">
      <p>{message}</p>
      {onRetry && <button onClick={onRetry}>إعادة المحاولة</button>}
    </div>
  )
}
