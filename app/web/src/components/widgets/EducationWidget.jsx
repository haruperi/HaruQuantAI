import React, { useState } from 'react';
import { educationCourses } from '../../mock/educationData';
import { docsData } from '../../mock/docsData';
import { ArrowUpRight, BookOpen, X, FileText, ChevronRight } from 'lucide-react';

export const EducationWidget = () => {
  const [selectedCat, setSelectedCat] = useState('Fundamentals');
  const [selectedDoc, setSelectedDoc] = useState(null);

  const categories = [
    'Fundamentals',
    'Development',
    'Robustness',
    'New to Futures',
    'Options',
    'Strategies',
    'Risk Management',
    'Financials',
    'Commodities'
  ];

  const docCategories = ['Fundamentals', 'Development', 'Robustness'];
  const isDocCategory = docCategories.includes(selectedCat);

  const filteredDocs = docsData.filter((d) => d.category === selectedCat);
  const filteredCourses = educationCourses.filter((c) => c.category === selectedCat);

  const handleCardClick = (item) => {
    if (isDocCategory) {
      setSelectedDoc(item);
    } else if (item.url) {
      window.open(item.url, '_blank', 'noopener,noreferrer');
    }
  };

  const renderFormattedMarkdown = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) return <div key={idx} style={{ height: '8px' }} />;
      if (trimmed.startsWith('# ')) {
        return (
          <h1 key={idx} style={{ color: 'var(--text-white, #fff)', fontSize: '22px', fontWeight: 700, margin: '20px 0 12px 0', borderBottom: '1px solid var(--border-color, #1e293b)', paddingBottom: '8px' }}>
            {trimmed.slice(2)}
          </h1>
        );
      }
      if (trimmed.startsWith('## ')) {
        return (
          <h2 key={idx} style={{ color: 'var(--cme-blue-cyan, #00c8ff)', fontSize: '17px', fontWeight: 600, margin: '16px 0 8px 0', borderBottom: '1px dashed rgba(255,255,255,0.1)', paddingBottom: '4px' }}>
            {trimmed.slice(3)}
          </h2>
        );
      }
      if (trimmed.startsWith('### ')) {
        return (
          <h3 key={idx} style={{ color: '#60a5fa', fontSize: '14px', fontWeight: 600, margin: '14px 0 6px 0' }}>
            {trimmed.slice(4)}
          </h3>
        );
      }
      if (trimmed.startsWith('#### ')) {
        return (
          <h4 key={idx} style={{ color: '#e2e8f0', fontSize: '13px', fontWeight: 600, margin: '10px 0 4px 0' }}>
            {trimmed.slice(5)}
          </h4>
        );
      }
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const content = trimmed.slice(2);
        return (
          <div key={idx} style={{ display: 'flex', gap: '8px', marginLeft: '12px', margin: '4px 0', fontSize: '13px', color: '#cbd5e1', lineHeight: '1.5' }}>
            <span style={{ color: 'var(--cme-blue-bright, #00A3E0)' }}>•</span>
            <div>{formatBoldText(content)}</div>
          </div>
        );
      }
      return (
        <p key={idx} style={{ fontSize: '13px', color: 'var(--text-muted-grey, #cbd5e1)', lineHeight: '1.6', margin: '6px 0' }}>
          {formatBoldText(trimmed)}
        </p>
      );
    });
  };

  const formatBoldText = (str) => {
    if (!str) return str;
    const parts = str.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} style={{ color: 'var(--text-white, #ffffff)', fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '16px 20px', background: 'var(--bg-main)', overflowY: 'auto' }}>
      {/* Category Pills & Top Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
        <div className="category-pills" style={{ background: 'transparent', padding: 0, border: 'none', margin: 0 }}>
          {categories.map((cat) => (
            <div
              key={cat}
              className={`category-pill ${selectedCat === cat ? 'active' : ''}`}
              onClick={() => setSelectedCat(cat)}
              style={{
                borderRadius: '16px',
                padding: '5px 14px',
                fontSize: '12px',
                fontWeight: 500
              }}
            >
              {cat}
            </div>
          ))}
        </div>

        <a
          href="https://www.cmegroup.com/education/courses.html"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: 'var(--cme-blue-cyan, #00c8ff)',
            fontSize: '13px',
            fontWeight: 500,
            textDecoration: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          <span>View Full Course Catalog</span>
          <ArrowUpRight size={15} />
        </a>
      </div>

      {/* Heading */}
      <h3 style={{ color: 'var(--text-white, #ffffff)', fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>
        {isDocCategory ? `${selectedCat} Documentation` : 'Courses'}
      </h3>

      {/* Grid of Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '14px',
          alignItems: 'stretch'
        }}
      >
        {isDocCategory
          ? filteredDocs.map((doc) => (
              <div
                key={doc.id}
                onClick={() => handleCardClick(doc)}
                style={{
                  background: 'var(--bg-card, #0b1a30)',
                  border: '1px solid var(--border-color, #162e50)',
                  borderRadius: 'var(--radius-md, 6px)',
                  padding: '18px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justify: 'space-between',
                  cursor: 'pointer',
                  minHeight: '160px',
                  transition: 'all 0.2s ease',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--cme-blue-bright, #00A3E0)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 6px 16px rgba(0, 163, 224, 0.15)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-color, #162e50)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '10px' }}>
                    <h4 style={{ color: 'var(--text-white, #ffffff)', fontSize: '14px', fontWeight: 700, lineHeight: '1.3' }}>
                      {doc.title}
                    </h4>
                    <FileText size={16} color="var(--cme-blue-cyan, #00c8ff)" style={{ flexShrink: 0, marginTop: '2px' }} />
                  </div>

                  <p style={{ fontSize: '12px', color: 'var(--text-muted-grey, #9ca3af)', lineHeight: '1.45', marginBottom: '14px' }}>
                    {doc.description}
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--cme-blue-bright, #00A3E0)' }}>
                    Read Module
                  </span>
                  <ChevronRight size={14} color="var(--cme-blue-bright, #00A3E0)" />
                </div>
              </div>
            ))
          : filteredCourses.map((course) => (
              <div
                key={course.id}
                onClick={() => handleCardClick(course)}
                style={{
                  background: 'var(--bg-card, #0b1a30)',
                  border: '1px solid var(--border-color, #162e50)',
                  borderRadius: 'var(--radius-md, 6px)',
                  padding: '18px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justify: 'space-between',
                  cursor: 'pointer',
                  minHeight: '160px',
                  transition: 'all 0.2s ease',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--cme-blue-bright, #00A3E0)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 6px 16px rgba(0, 163, 224, 0.15)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-color, #162e50)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '10px' }}>
                    <h4 style={{ color: 'var(--text-white, #ffffff)', fontSize: '14px', fontWeight: 700, lineHeight: '1.3' }}>
                      {course.title}
                    </h4>
                    <ArrowUpRight size={16} color="var(--cme-blue-cyan, #00c8ff)" style={{ flexShrink: 0, marginTop: '2px' }} />
                  </div>

                  <p style={{ fontSize: '12px', color: 'var(--text-muted-grey, #9ca3af)', lineHeight: '1.45', marginBottom: '14px' }}>
                    {course.description}
                  </p>
                </div>

                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--cme-blue-bright, #00A3E0)' }}>
                  {course.lessonsCount} Lessons
                </span>
              </div>
            ))}
      </div>

      {/* Full Documentation Viewer Modal */}
      {selectedDoc && (
        <div className="modal-overlay" onClick={() => setSelectedDoc(null)}>
          <div
            className="modal-content"
            style={{ width: '800px', maxWidth: '90vw', maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="modal-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px', borderBottom: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <FileText size={18} color="var(--cme-blue-cyan)" />
                <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-white)' }}>{selectedDoc.title}</span>
              </div>
              <button className="widget-btn" onClick={() => setSelectedDoc(null)} style={{ cursor: 'pointer', border: 'none', background: 'transparent', color: '#fff', fontSize: '16px' }}>✕</button>
            </div>

            {/* Modal Scrollable Body */}
            <div className="modal-body" style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', background: 'var(--bg-main)' }}>
              {renderFormattedMarkdown(selectedDoc.content)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
