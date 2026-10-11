import { newEducation, newExperience, newLink, newProject, newSkillGroup } from '../resumeDefaults'
import { AiEditable } from './AiEdit'
import { buttonStyles, Card, ItemCard, LinesField, TextArea, TextField } from './ui'

function listOps(items, put) {
  return {
    update: (index, patch) => put(items.map((item, i) => (i === index ? { ...item, ...patch } : item))),
    add: (item) => put([...items, item]),
    remove: (index) => put(items.filter((_, i) => i !== index)),
  }
}

function AddButton({ onClick, children }) {
  return (
    <button type="button" className={`${buttonStyles.secondary} w-full border-dashed`} onClick={onClick}>
      + {children}
    </button>
  )
}

// onChange must be a React state setter: AI edits finish asynchronously, so they apply
// through functional updates against the latest state rather than this render's copy.
export default function ResumeForm({ resume, onChange }) {
  const set = (key, value) => onChange({ ...resume, [key]: value })
  const setContact = (field, value) => set('contact', { ...resume.contact, [field]: value })

  // Swap one section (or one list entry) for its AI-edited version; siblings keep their identity.
  const replaceWhole = (key) => (target, next) =>
    onChange((prev) => (prev[key] === target ? { ...prev, [key]: next } : prev))
  const replaceEntry = (key) => (target, next) =>
    onChange((prev) => ({ ...prev, [key]: prev[key].map((item) => (item === target ? next : item)) }))

  const links = listOps(resume.contact.links, (v) => setContact('links', v))
  const skills = listOps(resume.skills, (v) => set('skills', v))
  const experience = listOps(resume.experience, (v) => set('experience', v))
  const education = listOps(resume.education, (v) => set('education', v))
  const projects = listOps(resume.projects, (v) => set('projects', v))
  const { contact } = resume

  return (
    <div className="space-y-4">
      <Card title="Contact">
        <div className="grid gap-3 sm:grid-cols-2">
          <TextField label="Full name" value={contact.name} onChange={(v) => setContact('name', v)} />
          <TextField label="Location" value={contact.location} onChange={(v) => setContact('location', v)} placeholder="City, Country" />
          <TextField label="Phone" value={contact.phone} onChange={(v) => setContact('phone', v)} />
          <TextField label="Email" type="email" value={contact.email} onChange={(v) => setContact('email', v)} />
        </div>
        <div className="mt-3 space-y-2">
          <span className="text-xs font-medium text-slate-600">Links</span>
          {contact.links.map((link, i) => (
            <div key={i} className="flex items-end gap-2">
              <div className="w-1/3">
                <TextField label="Label" value={link.label} onChange={(v) => links.update(i, { label: v })} placeholder="LinkedIn" />
              </div>
              <div className="flex-1">
                <TextField label="URL" value={link.url} onChange={(v) => links.update(i, { url: v })} placeholder="linkedin.com/in/you" />
              </div>
              <button type="button" className={`${buttonStyles.link} pb-2`} onClick={() => links.remove(i)}>
                Remove
              </button>
            </div>
          ))}
          <AddButton onClick={() => links.add(newLink())}>Add link</AddButton>
        </div>
      </Card>

      <AiEditable sectionName="summary" label="summary" data={resume.summary} onReplace={replaceWhole('summary')}>
        {({ button, panel }) => (
          <Card title="Summary" actions={button}>
            {panel}
            <TextArea label="Professional summary" rows={4} value={resume.summary} onChange={(v) => set('summary', v)} />
          </Card>
        )}
      </AiEditable>

      <AiEditable sectionName="skills" label="skills" data={resume.skills} onReplace={replaceWhole('skills')}>
        {({ button, panel }) => (
          <Card title="Skills" actions={button}>
            {panel}
            <div className="space-y-2">
              {resume.skills.map((group, i) => (
                <ItemCard key={i} title={group.category || `Skill group ${i + 1}`} onRemove={() => skills.remove(i)}>
                  <TextField label="Category" value={group.category} onChange={(v) => skills.update(i, { category: v })} placeholder="AI / ML" />
                  <TextField
                    label="Skills (comma-separated)"
                    value={group.items.join(', ')}
                    onChange={(v) => skills.update(i, { items: v.split(/, ?/) })}
                    placeholder="Python, PyTorch, LLMs"
                  />
                </ItemCard>
              ))}
              <AddButton onClick={() => skills.add(newSkillGroup())}>Add skill group</AddButton>
            </div>
          </Card>
        )}
      </AiEditable>

      <Card title="Experience">
        <div className="space-y-2">
          {resume.experience.map((job, i) => (
            <AiEditable
              key={i}
              sectionName="experience_entry"
              label={job.company || 'this position'}
              data={job}
              onReplace={replaceEntry('experience')}
            >
              {({ button, panel }) => (
                <ItemCard title={job.company || `Position ${i + 1}`} onRemove={() => experience.remove(i)} actions={button}>
                  {panel}
                  <div className="grid gap-2 sm:grid-cols-2">
                    <TextField label="Job title" value={job.title} onChange={(v) => experience.update(i, { title: v })} />
                    <TextField label="Company" value={job.company} onChange={(v) => experience.update(i, { company: v })} />
                    <TextField label="Location" value={job.location} onChange={(v) => experience.update(i, { location: v })} />
                    <div className="grid grid-cols-2 gap-2">
                      <TextField label="Start" value={job.start} onChange={(v) => experience.update(i, { start: v })} placeholder="Jan 2022" />
                      <TextField label="End" value={job.end} onChange={(v) => experience.update(i, { end: v })} placeholder="Present" />
                    </div>
                  </div>
                  <LinesField label="Bullet points" lines={job.bullets} onChange={(v) => experience.update(i, { bullets: v })} />
                </ItemCard>
              )}
            </AiEditable>
          ))}
          <AddButton onClick={() => experience.add(newExperience())}>Add position</AddButton>
        </div>
      </Card>

      <AiEditable sectionName="education" label="education" data={resume.education} onReplace={replaceWhole('education')}>
        {({ button, panel }) => (
          <Card title="Education" actions={button}>
            {panel}
            <div className="space-y-2">
              {resume.education.map((ed, i) => (
                <ItemCard key={i} title={ed.institution || `Education ${i + 1}`} onRemove={() => education.remove(i)}>
                  <div className="grid gap-2 sm:grid-cols-2">
                    <TextField label="Institution" value={ed.institution} onChange={(v) => education.update(i, { institution: v })} />
                    <TextField label="Degree" value={ed.degree} onChange={(v) => education.update(i, { degree: v })} />
                    <TextField label="Date" value={ed.date} onChange={(v) => education.update(i, { date: v })} placeholder="2020" />
                    <TextField label="GPA" value={ed.gpa} onChange={(v) => education.update(i, { gpa: v })} />
                  </div>
                </ItemCard>
              ))}
              <AddButton onClick={() => education.add(newEducation())}>Add education</AddButton>
            </div>
          </Card>
        )}
      </AiEditable>

      <Card title="Projects">
        <div className="space-y-2">
          {resume.projects.map((p, i) => (
            <AiEditable
              key={i}
              sectionName="project_entry"
              label={p.name || 'this project'}
              data={p}
              onReplace={replaceEntry('projects')}
            >
              {({ button, panel }) => (
                <ItemCard title={p.name || `Project ${i + 1}`} onRemove={() => projects.remove(i)} actions={button}>
                  {panel}
                  <div className="grid gap-2 sm:grid-cols-2">
                    <TextField label="Name" value={p.name} onChange={(v) => projects.update(i, { name: v })} />
                    <TextField label="Tech stack" value={p.stack} onChange={(v) => projects.update(i, { stack: v })} placeholder="FastAPI, React, MongoDB" />
                  </div>
                  <LinesField label="Bullet points" lines={p.bullets} onChange={(v) => projects.update(i, { bullets: v })} />
                </ItemCard>
              )}
            </AiEditable>
          ))}
          <AddButton onClick={() => projects.add(newProject())}>Add project</AddButton>
        </div>
      </Card>

      <AiEditable
        sectionName="accomplishments"
        label="accomplishments"
        data={resume.accomplishments}
        onReplace={replaceWhole('accomplishments')}
      >
        {({ button, panel }) => (
          <Card title="Accomplishments" actions={button}>
            {panel}
            <LinesField
              label="Awards, certifications, publications"
              lines={resume.accomplishments}
              onChange={(v) => set('accomplishments', v)}
            />
          </Card>
        )}
      </AiEditable>
    </div>
  )
}
