import { jsPDF } from 'jspdf'

/**
 * Generates and downloads a beautifully formatted, university-grade PDF
 * from structured study notes.
 *
 * @param {Object} note - The note object containing title, topic, content, key_points, examples, updated_at
 */
export function exportNoteToPDF(note) {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'pt',
    format: 'a4',
  })

  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 45
  const contentWidth = pageWidth - margin * 2

  let y = margin

  // Function to check page overflow and add new page if needed
  const ensureSpace = (neededHeight) => {
    if (y + neededHeight > pageHeight - margin - 30) {
      doc.addPage()
      y = margin + 15
      drawPageHeader()
    }
  }

  // Running Header on subsequent pages
  const drawPageHeader = () => {
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(148, 163, 184) // ink-400
    doc.text('AI Study Companion — Academic Study Notes', margin, margin - 10)
    doc.setDrawColor(226, 232, 240) // border
    doc.setLineWidth(0.5)
    doc.line(margin, margin - 5, pageWidth - margin, margin - 5)
  }

  // 1. Top Decorative Brand Bar
  doc.setFillColor(79, 70, 229) // Brand-600
  doc.rect(0, 0, pageWidth, 6, 'F')

  // 2. Document Super-title & Metadata Header
  y += 10
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9)
  doc.setTextColor(79, 70, 229)
  doc.text('AI STUDY COMPANION  •  ACADEMIC NOTES', margin, y)

  const dateStr = note.updated_at || new Date().toLocaleDateString('en-US', { dateStyle: 'medium' })
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(100, 116, 139)
  doc.text(dateStr, pageWidth - margin, y, { align: 'right' })

  // 3. Note Title
  y += 24
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(20)
  doc.setTextColor(15, 23, 42) // Ink-900

  const titleLines = doc.splitTextToSize(note.title || 'Untitled Study Note', contentWidth)
  doc.text(titleLines, margin, y)
  y += titleLines.length * 24

  // 4. Topic Badge / Chip
  const topicText = (note.topic || 'General Academic').toUpperCase()
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  const badgeWidth = doc.getTextWidth(topicText) + 16
  const badgeHeight = 16

  doc.setFillColor(238, 242, 255) // brand-50
  doc.setDrawColor(199, 210, 254) // brand-200
  doc.roundedRect(margin, y - 10, badgeWidth, badgeHeight, 3, 3, 'FD')

  doc.setTextColor(67, 56, 202) // brand-700
  doc.text(topicText, margin + 8, y + 1)

  y += 22

  // Horizontal divider
  doc.setDrawColor(226, 232, 240)
  doc.setLineWidth(1)
  doc.line(margin, y, pageWidth - margin, y)
  y += 20

  // 5. Key Points Box (if any)
  const keyPoints = Array.isArray(note.key_points) ? note.key_points : []
  if (keyPoints.length > 0) {
    ensureSpace(60)

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(11)
    doc.setTextColor(15, 23, 42)
    doc.text('KEY TAKEAWAYS & EXAM POINTS', margin, y)
    y += 14

    // Render Box container
    const boxStartY = y
    let boxContentY = boxStartY + 14

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.setTextColor(51, 65, 85)

    keyPoints.forEach((point) => {
      const bullet = '• '
      const fullText = bullet + point
      const lines = doc.splitTextToSize(fullText, contentWidth - 28)
      ensureSpace(lines.length * 13 + 6)
      doc.text(lines, margin + 14, boxContentY)
      boxContentY += lines.length * 13 + 4
    })

    const boxHeight = boxContentY - boxStartY + 8
    doc.setDrawColor(203, 213, 225)
    doc.setFillColor(248, 250, 252) // slate-50
    doc.roundedRect(margin, boxStartY, contentWidth, boxHeight, 4, 4, 'FD')

    // Re-draw text on top of fill
    boxContentY = boxStartY + 14
    keyPoints.forEach((point) => {
      const bullet = '• '
      const lines = doc.splitTextToSize(bullet + point, contentWidth - 28)
      doc.text(lines, margin + 14, boxContentY)
      boxContentY += lines.length * 13 + 4
    })

    y = boxStartY + boxHeight + 20
  }

  // 6. Main Detailed Content / Explanations
  ensureSpace(40)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(12)
  doc.setTextColor(15, 23, 42)
  doc.text('DETAILED CONCEPTS & ANALYSIS', margin, y)
  y += 14

  const rawContent = note.content || ''
  const paragraphs = rawContent.split('\n')

  paragraphs.forEach((p) => {
    const trimmed = p.trim()
    if (!trimmed) {
      y += 8
      return
    }

    // Markdown Heading 2 or 3
    if (trimmed.startsWith('## ') || trimmed.startsWith('### ')) {
      ensureSpace(30)
      y += 6
      const headingText = trimmed.replace(/^#+\s*/, '')
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(11)
      doc.setTextColor(79, 70, 229) // Brand color for headers
      doc.text(headingText, margin, y)
      y += 16
      return
    }

    // Bullet points
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || /^\d+\.\s/.test(trimmed)) {
      ensureSpace(20)
      const cleanBullet = trimmed.replace(/^[-*]\s+|\d+\.\s+/, '')
      const marker = trimmed.startsWith('- ') || trimmed.startsWith('* ') ? '• ' : trimmed.match(/^\d+\./)[0] + ' '
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9.5)
      doc.setTextColor(30, 41, 59)
      const lines = doc.splitTextToSize(marker + cleanBullet, contentWidth - 12)
      doc.text(lines, margin + 8, y)
      y += lines.length * 14 + 3
      return
    }

    // Regular paragraph
    ensureSpace(20)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9.5)
    doc.setTextColor(30, 41, 59)
    const lines = doc.splitTextToSize(trimmed, contentWidth)
    doc.text(lines, margin, y)
    y += lines.length * 14 + 4
  })

  // 7. Practical Examples Section (if any)
  const examples = Array.isArray(note.examples) ? note.examples : []
  if (examples.length > 0) {
    ensureSpace(45)
    y += 12
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(11)
    doc.setTextColor(15, 23, 42)
    doc.text('PRACTICAL EXAMPLES & CODE SNIPPETS', margin, y)
    y += 14

    examples.forEach((ex, idx) => {
      ensureSpace(35)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(9)
      doc.setTextColor(67, 56, 202)
      doc.text(`Example ${idx + 1}:`, margin, y)
      y += 12

      doc.setFont('courier', 'normal')
      doc.setFontSize(8.5)
      doc.setTextColor(30, 41, 59)
      const exLines = doc.splitTextToSize(ex, contentWidth - 16)

      const boxY = y - 4
      const boxH = exLines.length * 12 + 10

      doc.setFillColor(241, 245, 249) // slate-100
      doc.setDrawColor(203, 213, 225)
      doc.roundedRect(margin, boxY, contentWidth, boxH, 3, 3, 'FD')

      doc.text(exLines, margin + 8, y + 8)
      y = boxY + boxH + 12
    })
  }

  // 8. Footer on all pages
  const totalPages = doc.internal.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(148, 163, 184)
    doc.setDrawColor(226, 232, 240)
    doc.setLineWidth(0.5)
    doc.line(margin, pageHeight - margin + 10, pageWidth - margin, pageHeight - margin + 10)
    doc.text('Generated with AI Study Companion • Verified Academic Notes', margin, pageHeight - margin + 22)
    doc.text(`Page ${i} of ${totalPages}`, pageWidth - margin, pageHeight - margin + 22, { align: 'right' })
  }

  // Save the generated PDF
  const safeFilename = (note.title || 'Study_Notes')
    .replace(/[^a-zA-Z0-9_-]/g, '_')
    .slice(0, 40)
  doc.save(`${safeFilename}_Notes.pdf`)
}

/**
 * Generates and downloads a beautifully styled PDF from a structured study summary.
 *
 * @param {Object} summary - The summary object containing materialTitle, generatedAt, keyConcepts, sections
 * @param {string} materialTitle - Fallback title of the material
 */
export function exportSummaryToPDF(summary, materialTitle = 'Study Material') {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'pt',
    format: 'a4',
  })

  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 45
  const contentWidth = pageWidth - margin * 2

  let y = margin

  const ensureSpace = (neededHeight) => {
    if (y + neededHeight > pageHeight - margin - 30) {
      doc.addPage()
      y = margin + 15
      drawPageHeader()
    }
  }

  const drawPageHeader = () => {
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(148, 163, 184)
    doc.text('AI Study Companion — Executive Study Summary', margin, margin - 10)
    doc.setDrawColor(226, 232, 240)
    doc.setLineWidth(0.5)
    doc.line(margin, margin - 5, pageWidth - margin, margin - 5)
  }

  // Top Decorative Brand Bar
  doc.setFillColor(79, 70, 229)
  doc.rect(0, 0, pageWidth, 6, 'F')

  // Super-title & Metadata Header
  y += 10
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(9)
  doc.setTextColor(79, 70, 229)
  doc.text('AI STUDY COMPANION  •  EXECUTIVE SUMMARY', margin, y)

  const dateStr = summary.generatedAt || new Date().toLocaleDateString('en-US', { dateStyle: 'medium' })
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(100, 116, 139)
  doc.text(`Generated: ${dateStr}`, pageWidth - margin, y, { align: 'right' })

  // Document Title
  y += 24
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(20)
  doc.setTextColor(15, 23, 42)
  const title = summary.materialTitle || materialTitle || 'Document Summary'
  const titleLines = doc.splitTextToSize(title, contentWidth)
  doc.text(titleLines, margin, y)
  y += titleLines.length * 22

  // Key Concepts chips / bar
  if (summary.keyConcepts && summary.keyConcepts.length > 0) {
    ensureSpace(40)
    y += 10
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(10)
    doc.setTextColor(79, 70, 229)
    doc.text('CORE CONCEPTS & DEFINITIONS', margin, y)
    y += 14

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.setTextColor(51, 65, 85)
    const conceptsText = summary.keyConcepts.join('  •  ')
    const conceptsLines = doc.splitTextToSize(conceptsText, contentWidth)
    doc.text(conceptsLines, margin, y)
    y += conceptsLines.length * 13 + 12
  }

  // Divider
  doc.setDrawColor(226, 232, 240)
  doc.setLineWidth(1)
  doc.line(margin, y, pageWidth - margin, y)
  y += 18

  // Sections
  const sections = summary.sections || []
  sections.forEach((sec, idx) => {
    ensureSpace(60)

    // Section Title
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(13)
    doc.setTextColor(30, 41, 59)
    doc.text(`${idx + 1}. ${sec.title}`, margin, y)
    y += 18

    // Section Body
    if (sec.body) {
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9.5)
      doc.setTextColor(71, 85, 105)
      const bodyLines = doc.splitTextToSize(sec.body, contentWidth)
      ensureSpace(bodyLines.length * 13 + 10)
      doc.text(bodyLines, margin, y)
      y += bodyLines.length * 13 + 8
    }

    // Section Points
    if (sec.points && sec.points.length > 0) {
      sec.points.forEach((pt) => {
        const ptLines = doc.splitTextToSize(pt, contentWidth - 16)
        ensureSpace(ptLines.length * 12 + 6)
        doc.setFillColor(79, 70, 229)
        doc.circle(margin + 5, y - 3, 2, 'F')
        doc.setFont('helvetica', 'normal')
        doc.setFontSize(9)
        doc.setTextColor(30, 41, 59)
        doc.text(ptLines, margin + 14, y)
        y += ptLines.length * 12 + 4
      })
    }

    y += 14
  })

  // Footers
  const totalPages = doc.internal.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(148, 163, 184)
    doc.setDrawColor(226, 232, 240)
    doc.setLineWidth(0.5)
    doc.line(margin, pageHeight - margin + 10, pageWidth - margin, pageHeight - margin + 10)
    doc.text('AI Study Companion • AI Generated Summary Notes', margin, pageHeight - margin + 22)
    doc.text(`Page ${i} of ${totalPages}`, pageWidth - margin, pageHeight - margin + 22, { align: 'right' })
  }

  const safeFilename = title.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 40)
  doc.save(`${safeFilename}_Summary.pdf`)
}

