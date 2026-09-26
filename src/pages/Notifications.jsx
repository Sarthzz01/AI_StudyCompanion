import { useState } from 'react'
import { BellOff, CheckCheck, Trash2 } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Button from '../components/Button.jsx'
import NotificationItem from '../components/NotificationItem.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { useStudyData } from '../context/StudyDataContext.jsx'
import { useToast } from '../context/ToastContext.jsx'

const filters = ['All', 'Unread']

export default function Notifications() {
  const { notifications, unreadCount, markNotificationRead, markAllNotificationsRead, clearNotifications } =
    useStudyData()
  const toast = useToast()
  const [filter, setFilter] = useState('All')

  const visible = filter === 'Unread' ? notifications.filter((n) => !n.read) : notifications

  return (
    <>
      <PageHeader
        title="Notifications"
        subtitle={unreadCount ? `${unreadCount} unread` : 'You are all caught up.'}
        actions={
          <>
            <Button
              variant="secondary"
              icon={CheckCheck}
              onClick={() => {
                markAllNotificationsRead()
                toast('All notifications marked read', 'success')
              }}
              disabled={unreadCount === 0}
            >
              Mark all read
            </Button>
            <Button
              variant="ghost"
              icon={Trash2}
              onClick={() => {
                clearNotifications()
                toast('Notifications cleared', 'success')
              }}
              disabled={notifications.length === 0}
            >
              Clear
            </Button>
          </>
        }
      />

      <div className="mb-5 flex gap-2">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              filter === f
                ? 'bg-brand-600 text-white'
                : 'bg-ink-100 text-ink-600 hover:bg-ink-200 dark:bg-ink-800 dark:text-ink-300'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <EmptyState
          icon={BellOff}
          title={filter === 'Unread' ? 'Nothing unread' : 'No notifications'}
          description="Quiz results, new recommendations and completed goals show up here."
        />
      ) : (
        <div className="space-y-3">
          {visible.map((n) => (
            <NotificationItem key={n.id} notification={n} onMarkRead={markNotificationRead} />
          ))}
        </div>
      )}
    </>
  )
}
