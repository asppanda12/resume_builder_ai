// Mirrors the backend's canonical resume schema (spec §5).
export const newLink = () => ({ label: '', url: '' })
export const newSkillGroup = () => ({ category: '', items: [] })
export const newExperience = () => ({ company: '', title: '', location: '', start: '', end: '', bullets: [] })
export const newEducation = () => ({ institution: '', degree: '', date: '', gpa: '' })
export const newProject = () => ({ name: '', stack: '', bullets: [] })

export const emptyResume = () => ({
  contact: { name: '', location: '', phone: '', email: '', links: [] },
  summary: '',
  skills: [],
  experience: [],
  education: [],
  projects: [],
  accomplishments: [],
})
