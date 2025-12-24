import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'
import Editor from '@monaco-editor/react'
import '@fortawesome/fontawesome-free/css/all.min.css'
import { getLessonDetail, submitLessonSolution, getCourseBySlug } from '../../apis/lesson.api'
import TopLesson from '../TopLesson'
import './style.scss'

const LANGUAGE_MAP = {
  python: 'python',
  cpp: 'cpp',
  java: 'java',
  javascript: 'javascript',
  go: 'go',
}

const Lesson = () => {
  const { IDslug, IDlesson } = useParams()
  const navigate = useNavigate()
  const [lessonData, setLessonData] = useState(null)
  const [loading, setLoading] = useState(true)

  // Quiz State
  const [selectedAnswers, setSelectedAnswers] = useState({})

  // Judge State
  const [code, setCode] = useState('')
  const [runOutput, setRunOutput] = useState(null)
  const [selectedLanguage, setSelectedLanguage] = useState(null)
  const [selectedLanguageKey, setSelectedLanguageKey] = useState('python')
  const [submitting, setSubmitting] = useState(false)
  const [consoleTab, setConsoleTab] = useState('test') // 'test', 'sample', or 'status'
  const [isSubmitMode, setIsSubmitMode] = useState(false)

  // Navigation State
  const [nextLessonUrl, setNextLessonUrl] = useState(null)
  const [prevLessonUrl, setPrevLessonUrl] = useState(null)

  // Reset states when lesson changes
  useEffect(() => {
    setRunOutput(null)
    setConsoleTab('test')
    setIsSubmitMode(false)
    setSelectedAnswers({})
  }, [IDlesson])

  // Navigation logic
  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        const courseData = await getCourseBySlug(IDslug)
        let lessons = []
        if (courseData.lessons && Array.isArray(courseData.lessons)) {
          lessons = courseData.lessons
        } else if (courseData.chapters && Array.isArray(courseData.chapters)) {
          lessons = courseData.chapters.flatMap((ch) => ch.lessons || [])
        } else if (Array.isArray(courseData)) {
          lessons = courseData
        }

        const currentSlug = IDlesson.replace(/\/$/, '').toLowerCase()
        const currentIndex = lessons.findIndex((l) => {
          const lessonSlug = (l.slug || '').replace(/\/$/, '').toLowerCase()
          return lessonSlug === currentSlug
        })

        if (currentIndex !== -1) {
          if (currentIndex < lessons.length - 1) {
            const nextSlug = lessons[currentIndex + 1].slug.replace(/\/$/, '')
            setNextLessonUrl(`/${IDslug}/${nextSlug}`)
          } else {
            setNextLessonUrl('LAST_LESSON')
          }

          if (currentIndex > 0) {
            const prevSlug = lessons[currentIndex - 1].slug.replace(/\/$/, '')
            setPrevLessonUrl(`/${IDslug}/${prevSlug}`)
          } else {
            setPrevLessonUrl('FIRST_LESSON')
          }
        }
      } catch (error) {
        console.error('Failed to fetch course data for navigation', error)
      }
    }
    if (IDslug && IDlesson) fetchCourseData()
  }, [IDslug, IDlesson])

  const handleNext = () => {
    if (nextLessonUrl === 'LAST_LESSON') {
      toast.success('You have completed the final lesson!')
      navigate(`/${IDslug}`)
    } else if (nextLessonUrl) {
      navigate(nextLessonUrl)
    } else {
      navigate(`/${IDslug}`)
    }
  }

  const handleBack = () => {
    if (prevLessonUrl === 'FIRST_LESSON' || !prevLessonUrl) {
      navigate(`/${IDslug}`)
    } else if (prevLessonUrl) {
      navigate(prevLessonUrl)
    }
  }

  useEffect(() => {
    const fetchLessonData = async () => {
      try {
        setLoading(true)
        const response = await getLessonDetail(IDslug, IDlesson)
        setLessonData(response)

        if (response.problem?.allowed_languages?.length > 0) {
          const defaultLang = response.problem.allowed_languages[0]
          setSelectedLanguage(defaultLang.id)
          setSelectedLanguageKey(defaultLang.key)
          setCode(defaultLang.starter_code || response.problem.starter_code || '')
        } else {
          setCode('')
        }
      } catch {
        toast.error('Could not load lesson content')
      } finally {
        setLoading(false)
      }
    }
    if (IDslug && IDlesson) fetchLessonData()
  }, [IDslug, IDlesson])

  const handleLanguageChange = (lang) => {
    setSelectedLanguage(lang.id)
    setSelectedLanguageKey(lang.key)
    if (lang.starter_code) {
      setCode(lang.starter_code)
    }
  }

  const handleOptionChange = (qId, cId) => {
    setSelectedAnswers((prev) => ({ ...prev, [qId]: cId }))
  }

  const handleQuizSubmit = async () => {
    if (submitting) return

    const answers = Object.entries(selectedAnswers).map(([qId, cId]) => ({
      question: qId,
      selected_choice_id: cId,
    }))

    if (answers.length === 0) {
      toast.error('Please answer the question')
      return
    }

    try {
      setSubmitting(true)
      const response = await submitLessonSolution(IDslug, IDlesson, { answers })

      if (response.passed) {
        toast.success('Congratulations! You passed the quiz.')
        setLessonData((prev) => ({
          ...prev,
          progress: { ...prev.progress, status: 'completed' },
        }))
        if (nextLessonUrl && nextLessonUrl !== 'LAST_LESSON') {
          setTimeout(() => navigate(nextLessonUrl), 1500)
        }
      } else {
        toast.error('Incorrect. Please try again.')
      }
    } catch (error) {
      toast.error('Error submitting quiz')
      console.error(error)
    } finally {
      setSubmitting(false)
    }
  }

  const executeCode = async (isFinalSubmit) => {
    if (submitting) return
    if (!selectedLanguage) {
      toast.error('Please select a language')
      return
    }

    try {
      setSubmitting(true)
      setRunOutput(null)
      setIsSubmitMode(isFinalSubmit)
      const payload = {
        language: selectedLanguageKey,
        code: code,
      }

      const response = await submitLessonSolution(IDslug, IDlesson, payload)

      const finalResult = response.summary || response
      if (response.status) finalResult.final_status = response.status
      setRunOutput(finalResult)

      if (response.passed || finalResult.final_status === 'ac') {
        toast.success(isFinalSubmit ? 'Correct! Lesson Completed.' : 'All tests passed!')
        if (isFinalSubmit) {
          setLessonData((prev) => ({
            ...prev,
            progress: { ...prev.progress, status: 'completed' },
          }))
          if (nextLessonUrl && nextLessonUrl !== 'LAST_LESSON') {
            setTimeout(() => navigate(nextLessonUrl), 1500)
          }
        }
      } else {
        const statusMap = {
          wa: 'Wrong Answer',
          tle: 'Time Limit Exceeded',
          ce: 'Compilation Error',
          re: 'Runtime Error',
        }
        toast.error(
          `Result: ${statusMap[finalResult.final_status] || finalResult.final_status || 'Failed'}`,
        )
      }
    } catch (error) {
      toast.error('Error processing execution')
      console.error(error)
    } finally {
      setSubmitting(false)
    }
  }

  const renderQuizLayout = () => (
    <div className='lesson__judge-layout'>
      <div className='lesson__left'>
        <div className='lesson__header'>
          <h1>{lessonData.title}</h1>
          <span className='status-badge'>{lessonData.progress?.status || 'incomplete'}</span>
        </div>
        <div className='markdown-content'>
          <ReactMarkdown>{lessonData.content_md}</ReactMarkdown>
        </div>
      </div>

      <div className='lesson__right quiz-mode-container'>
        <div className='quiz-wrapper'>
          {(lessonData.quiz?.questions || lessonData.questions || []).map((question, idx) => (
            <div key={question.id} className='quiz-card'>
              <p className='quiz-question'>
                <strong>Question {idx + 1}:</strong> {question.text}
              </p>
              <div className='quiz-options'>
                {(question.choices || question.options || []).map((choice) => (
                  <label
                    key={choice.id}
                    className={`option ${selectedAnswers[question.id] === choice.id ? 'active' : ''}`}>
                    <input
                      type='radio'
                      name={question.id}
                      className='hidden-radio'
                      onChange={() => handleOptionChange(question.id, choice.id)}
                      checked={selectedAnswers[question.id] === choice.id}
                    />
                    <span className='option-text'>{choice.text}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
          <div className='quiz-footer'>
            <button className='btn-submit-quiz' onClick={handleQuizSubmit} disabled={submitting}>
              <span>{submitting ? 'Submitting...' : 'Submit Now'}</span>
              <i className='fa-solid fa-paper-plane'></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  const renderJudgeLayout = () => (
    <div className='lesson__judge-layout'>
      <div className='lesson__left'>
        <div className='lesson__header'>
          <h1>{lessonData.title}</h1>
          <span className='status-badge'>Judge Mode</span>
        </div>
        <div className='markdown-content'>
          <ReactMarkdown>{lessonData.content_md}</ReactMarkdown>
        </div>
        {lessonData.problem && (
          <div className='problem-statement'>
            <h3>Requirements</h3>
            <p>
              <strong>Challenge:</strong> {lessonData.problem.title}
            </p>
            <div className='allowed-langs'>
              {lessonData.problem.allowed_languages?.map((l) => (
                <span
                  key={l.id}
                  className={`lang-tag ${selectedLanguage === l.id ? 'active' : ''}`}
                  onClick={() => handleLanguageChange(l)}
                  style={{ cursor: 'pointer' }}>
                  {l.key}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className='lesson__right'>
        <div
          className='editor-wrapper'
          style={{ height: '60%', display: 'flex', flexDirection: 'column' }}>
          <div className='editor-header'>
            <span>
              <i className='fa-solid fa-code'></i> main.
              {selectedLanguageKey === 'python' ? 'py' : 'cpp'}
            </span>
          </div>
          <div style={{ flex: 1 }}>
            <Editor
              height='100%'
              language={LANGUAGE_MAP[selectedLanguageKey] || 'plaintext'}
              value={code}
              theme='vs-dark'
              onChange={(val) => setCode(val)}
              options={{ minimap: { enabled: false }, fontSize: 16, automaticLayout: true }}
            />
          </div>
        </div>
        <div className='test-case-wrapper' style={{ height: '40%' }}>
          <div className='test-case-header'>
            <div className='console-tabs'>
              <span
                className={consoleTab === 'test' ? 'active' : ''}
                onClick={() => setConsoleTab('test')}>
                <i className='fa-solid fa-terminal'></i> Test Cases
              </span>
              <span
                className={consoleTab === 'sample' ? 'active' : ''}
                onClick={() => setConsoleTab('sample')}>
                <i className='fa-solid fa-vials'></i> Sample
              </span>
              <span
                className={consoleTab === 'status' ? 'active' : ''}
                onClick={() => setConsoleTab('status')}>
                <i className='fa-solid fa-circle-info'></i> Details
              </span>
            </div>
            <div className='actions'>
              <button
                onClick={() => {
                  setIsSubmitMode(false)
                  executeCode(false)
                }}
                className='btn-run'
                disabled={submitting}>
                <i className='fa-solid fa-play'></i> Run
              </button>
              <button
                className='btn-submit'
                onClick={() => {
                  setIsSubmitMode(true)
                  executeCode(true)
                }}
                disabled={submitting}>
                <i className='fa-solid fa-cloud-arrow-up'></i> Submit
              </button>
            </div>
          </div>
          <div className='test-case-content'>
            {consoleTab === 'sample' ? (
              <div className='console-output'>
                <div className='status-details'>
                  {(() => {
                    const samples = lessonData?.problem?.sample_testcases || []

                    if (samples.length === 0) return <p>No sample data available.</p>

                    return samples.map((sample, idx) => (
                      <div key={sample.id || idx} style={{ marginBottom: '20px' }}>
                        {samples.length > 1 && (
                          <div style={{ marginBottom: '10px', opacity: 0.7, fontSize: '0.8em', textTransform: 'uppercase' }}>
                            Sample Case #{idx + 1}
                          </div>
                        )}
                        <div className='detail-section'>
                          <div className='detail-label'>
                            <i className='fa-solid fa-file-import'></i>
                            <span>Sample Input</span>
                          </div>
                          <pre className='stdout-box'>{sample.input_data || '(no input)'}</pre>
                        </div>
                        <div className='detail-section'>
                          <div className='detail-label'>
                            <i className='fa-solid fa-file-export'></i>
                            <span>Expected Output</span>
                          </div>
                          <pre className='stdout-box'>{sample.expected_output || '(no expected output)'}</pre>
                        </div>
                      </div>
                    ))
                  })()}
                </div>
              </div>
            ) : runOutput ? (
              <div className='console-output'>
                {consoleTab === 'test' ? (
                  <>
                    <div className='console-status'>
                      <strong>Final Status: </strong>
                      <span
                        className={`status-${(runOutput.final_status || (runOutput.passed ? 'ac' : 'wa')).toLowerCase()}`}>
                        {runOutput.final_status || (runOutput.passed ? 'AC' : 'WA')}
                      </span>
                    </div>

                    {runOutput.tests && runOutput.tests.length > 0 ? (
                      <div className='test-cases-list'>
                        {isSubmitMode
                          ? runOutput.tests.map((tc, index) => {
                              const isPassed = tc.status === 'ac'
                              const label = index === 0 ? 'Sample Test' : `Test ${index}`
                              const isUnhidden = !tc.hidden

                              return (
                                <div key={index} className='test-case-container'>
                                  <div
                                    className={`test-case-item ${isPassed ? 'passed' : 'failed'}`}>
                                    <span>{label}:</span>
                                    {isPassed ? (
                                      <i className='fa-solid fa-check icon-v'></i>
                                    ) : (
                                      <i className='fa-solid fa-times icon-x'></i>
                                    )}
                                    {tc.runtime_ms && (
                                      <small style={{ marginLeft: 'auto', opacity: 0.6 }}>
                                        {tc.runtime_ms}ms
                                      </small>
                                    )}
                                  </div>
                                  {isUnhidden && (
                                    <div className='test-case-details-mini'>
                                      {tc.stdout && (
                                        <div className='mini-row'>
                                          <strong>Your Output:</strong> <code>{tc.stdout}</code>
                                        </div>
                                      )}
                                      {tc.stderr && (
                                        <div className='mini-row'>
                                          <strong>Error:</strong> <code>{tc.stderr}</code>
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              )
                            })
                          : runOutput.tests
                              .filter((t) => !t.hidden)
                              .slice(0, 1)
                              .map((tc, index) => {
                                const isPassed = tc.status === 'ac'
                                return (
                                  <div key={index} className='test-case-container'>
                                    <div
                                      className={`test-case-item ${isPassed ? 'passed' : 'failed'}`}>
                                      <span>Sample Test:</span>
                                      {isPassed ? (
                                        <i className='fa-solid fa-check icon-v'></i>
                                      ) : (
                                        <i className='fa-solid fa-times icon-x'></i>
                                      )}
                                      {tc.runtime_ms && (
                                        <small style={{ marginLeft: 'auto', opacity: 0.6 }}>
                                          {tc.runtime_ms}ms
                                        </small>
                                      )}
                                    </div>
                                    <div className='test-case-details-mini'>
                                      {tc.stdout && (
                                        <div className='mini-row'>
                                          <strong>Your Output:</strong> <code>{tc.stdout}</code>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )
                              })}
                      </div>
                    ) : (
                      <p>No test cases found in results.</p>
                    )}
                  </>
                ) : (
                  <div className='status-details'>
                    {(() => {
                      const tests = Array.isArray(runOutput.tests) ? runOutput.tests : []
                      const firstFailed = tests.find((t) => t.status !== 'ac')
                      const firstTest = tests[0]
                      const targetTest = firstFailed || firstTest

                      const displayStderr =
                        runOutput.stderr || runOutput.compile_output || targetTest?.stderr
                      const isAc =
                        (runOutput.final_status || runOutput.status || '').toLowerCase() === 'ac'

                      return (
                        <div className='detail-section'>
                          <div className='detail-label error'>
                            <i className='fa-solid fa-triangle-exclamation'></i>
                            <span>Error Log</span>
                          </div>
                          <pre className='stderr-box'>
                            {displayStderr ||
                              (isAc ? '(no errors)' : 'No error details available.')}
                          </pre>
                        </div>
                      )
                    })()}
                  </div>
                )}
              </div>
            ) : (
              <div className='empty-state'>Ready to run</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )

  if (loading) return <div className='loading-screen'>Loading lesson...</div>

  return (
    <>
      <TopLesson
        onNext={handleNext}
        hasNext={!!nextLessonUrl}
        onBack={handleBack}
        hasPrev={!!prevLessonUrl}
        nextDisabled={lessonData?.progress?.status !== 'completed'}
      />
      <div className='lesson-container'>
        {lessonData?.type?.toLowerCase() === 'quiz' ? renderQuizLayout() : renderJudgeLayout()}
      </div>
    </>
  )
}

export default Lesson
