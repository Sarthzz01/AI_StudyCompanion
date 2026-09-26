import { useState } from 'react'
import { Plus, Target, Check, Trash2 } from 'lucide-react'
import PageHeader from '../components/PageHeader.jsx'
import Card, { CardHeader } from '../components/Card.jsx'
import Button from '../components/Button.jsx'
import Input from '../components/Input.jsx'
import Select from '../components/Select.jsx'
import Modal from '../components/Modal.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { useStudyData } from '../context/StudyDataContext.jsx'
import { useToast } from '../context/ToastContext.jsx'

const emptyGoal = { title: '', type: 'weekly', target: 5, unit: 'topics' }

export default function Goals() {
  const { goals, addGoal, completeGoal, removeGoal } = useStudyData()
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState(emptyGoal)
  const [errors, setErrors] = useState({})

  const save = () => {
    const next = {}
    if (!draft.title.trim()) next.title = 'Give the goal a name.'
    if (!draft.target || Number(draft.target) < 1) next.target = 'The target must be at least 1.'
    setErrors(next)
    if (Object.keys(next).length) return

    addGoal({ ...draft, target: Number(draft.target) })
    toast('Goal added', 'success')
    setDraft(emptyGoal)
    setOpen(false)
  }

  const daily = goals.filter((g) => g.type === 'daily')
  const weekly = goals.filter((g) => g.type === 'weekly')

  const GoalList = ({ items }) =>
    items.length === 0 ? (
      <p className="muted">No goals in this group yet.</p>
    ) : (
      <div className="space-y-4">
        {items.map((goal) => (
          <div key={goal.id} className="rounded-xl border border-ink-200 p-4 dark:border-ink-800">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{goal.title}</p>
                <p className="muted mt-0.5">
                  {goal.current} of {goal.target} {goal.unit}
                </p>
              </div>
              <div className="flex items-center gap-1">
                {goal.completed ? (
                  <span className="chip bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
                    <Check size={12} /> Done
                  </span>
                ) : (
                  <Button size="sm" variant="secondary" icon={Check} onClick={() => completeGoal(goal.id)}>
                    Complete
                  </Button>
                )}
                <button
                  onClick={() => removeGoal(goal.id)}
                  aria-label={`Delete ${goal.title}`}
                  className="rounded-lg p-2 text-ink-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
            <div className="mt-3">
              <ProgressBar
                value={(goal.current / goal.target) * 100}
                tone={goal.completed ? 'emerald' : 'brand'}
                size="sm"
              />
            </div>
          </div>
        ))}
      </div>
    )

  return (
    <>
      <PageHeader
        title="Goals"
        subtitle="Small targets that keep the week moving."
        actions={
          <Button icon={Plus} onClick={() => setOpen(true)}>
            Add goal
          </Button>
        }
      />

      {goals.length === 0 ? (
        <EmptyState
          icon={Target}
          title="No goals yet"
          description="Set a daily or weekly target and track it here."
          actionLabel="Add your first goal"
          onAction={() => setOpen(true)}
        />
      ) : (
        <div className="grid gap-5 lg:grid-cols-2">
          <Card>
            <CardHeader title="Daily goals" subtitle="Reset every morning" />
            <GoalList items={daily} />
          </Card>
          <Card>
            <CardHeader title="Weekly goals" subtitle="Reset every Monday" />
            <GoalList items={weekly} />
          </Card>
        </div>
      )}

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Add a goal"
        description="Keep it specific enough to tick off."
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={save}>Add goal</Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Goal"
            placeholder="e.g. Complete 5 topics"
            value={draft.title}
            onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
            error={errors.title}
          />
          <div className="grid gap-4 sm:grid-cols-3">
            <Select
              label="Type"
              options={[
                { value: 'daily', label: 'Daily' },
                { value: 'weekly', label: 'Weekly' },
              ]}
              value={draft.type}
              onChange={(e) => setDraft((d) => ({ ...d, type: e.target.value }))}
            />
            <Input
              label="Target"
              type="number"
              min="1"
              value={draft.target}
              onChange={(e) => setDraft((d) => ({ ...d, target: e.target.value }))}
              error={errors.target}
            />
            <Select
              label="Unit"
              options={['topics', 'minutes', 'quizzes', 'flashcards']}
              value={draft.unit}
              onChange={(e) => setDraft((d) => ({ ...d, unit: e.target.value }))}
            />
          </div>
        </div>
      </Modal>
    </>
  )
}
