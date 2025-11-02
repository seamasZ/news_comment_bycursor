import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'
import { FileDown, History, Globe, Loader2, CheckCircle2, XCircle } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

function App() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState([])
  const [showHistory, setShowHistory] = useState(false)
  const [commentConfig, setCommentConfig] = useState({
    count: 10,
    styles: { formal: 0.3, casual: 0.3, humorous: 0.2, analytical: 0.1, emotional: 0.1 },
    perspectives: { positive: 0.4, neutral: 0.4, negative: 0.2 }
  })

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/history`)
      if (response.data.success) {
        setHistory(response.data.data)
      }
    } catch (err) {
      console.error('加载历史记录失败:', err)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!url.trim()) {
      setError('请输入有效的URL')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${API_BASE}/api/generate`, {
        url: url,
        comment_config: commentConfig
      })

      if (response.data.success) {
        setResult(response.data.data)
        loadHistory()
      } else {
        setError('生成失败，请重试')
      }
    } catch (err) {
      console.error('生成错误:', err)
      let errorMessage = '生成失败，请检查URL是否正确或稍后重试'
      
      if (err.response) {
        // 服务器返回了错误响应
        errorMessage = err.response.data?.detail || err.response.data?.message || `服务器错误: ${err.response.status}`
      } else if (err.request) {
        // 请求发送了但没有收到响应
        errorMessage = '无法连接到服务器，请确保后端服务正在运行 (http://localhost:8000)'
      } else {
        // 其他错误
        errorMessage = err.message || errorMessage
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (recordId) => {
    try {
      const response = await axios.get(`${API_BASE}/api/export/${recordId}`, {
        responseType: 'blob'
      })
      
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `comments_${recordId}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      alert('导出失败，请重试')
    }
  }

  const loadRecord = async (recordId) => {
    try {
      const response = await axios.get(`${API_BASE}/api/history/${recordId}`)
      if (response.data.success) {
        setResult(response.data.data)
        setShowHistory(false)
      }
    } catch (err) {
      alert('加载记录失败')
    }
  }

  const updateStyleRatio = (style, value) => {
    setCommentConfig(prev => ({
      ...prev,
      styles: {
        ...prev.styles,
        [style]: parseFloat(value) || 0
      }
    }))
  }

  const updatePerspectiveRatio = (perspective, value) => {
    setCommentConfig(prev => ({
      ...prev,
      perspectives: {
        ...prev.perspectives,
        [perspective]: parseFloat(value) || 0
      }
    }))
  }

  return (
    <div className="app">
      <header className="header">
        <h1>
          <Globe className="icon" />
          新闻评论生成系统
        </h1>
        <button 
          className="history-btn"
          onClick={() => setShowHistory(!showHistory)}
        >
          <History size={20} />
          历史记录
        </button>
      </header>

      <div className="container">
        {showHistory && (
          <div className="history-panel">
            <h2>历史记录</h2>
            <div className="history-list">
              {history.length === 0 ? (
                <p className="empty">暂无历史记录</p>
              ) : (
                history.map(record => (
                  <div key={record.id} className="history-item">
                    <div className="history-info">
                      <h3>{record.title}</h3>
                      <p className="history-url">{record.url}</p>
                      <p className="history-date">{new Date(record.created_at).toLocaleString('zh-CN')}</p>
                    </div>
                    <div className="history-actions">
                      <button onClick={() => loadRecord(record.id)}>查看</button>
                      <button onClick={() => handleExport(record.id)}>
                        <FileDown size={16} />
                        导出CSV
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        <div className="main-content">
          <form onSubmit={handleSubmit} className="input-form">
            <div className="input-group">
              <label htmlFor="url">新闻URL链接</label>
              <input
                id="url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="请输入新闻网页URL，例如：https://example.com/news"
                required
              />
            </div>

            <div className="config-section">
              <h3>评论生成配置</h3>
              
              <div className="config-item">
                <label>评论数量：</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={commentConfig.count}
                  onChange={(e) => setCommentConfig(prev => ({ ...prev, count: parseInt(e.target.value) || 10 }))}
                />
              </div>

              <div className="config-group">
                <label>语言风格分布：</label>
                <div className="ratio-inputs">
                  {Object.entries(commentConfig.styles).map(([style, ratio]) => (
                    <div key={style} className="ratio-input">
                      <label>{style === 'formal' ? '正式' : style === 'casual' ? '随意' : style === 'humorous' ? '幽默' : style === 'analytical' ? '分析' : '情感'}</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={ratio}
                        onChange={(e) => updateStyleRatio(style, e.target.value)}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="config-group">
                <label>观点倾向分布：</label>
                <div className="ratio-inputs">
                  {Object.entries(commentConfig.perspectives).map(([perspective, ratio]) => (
                    <div key={perspective} className="ratio-input">
                      <label>{perspective === 'positive' ? '积极' : perspective === 'neutral' ? '中性' : '消极'}</label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={ratio}
                        onChange={(e) => updatePerspectiveRatio(perspective, e.target.value)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <button type="submit" disabled={loading} className="submit-btn">
              {loading ? (
                <>
                  <Loader2 className="spin" size={20} />
                  生成中...
                </>
              ) : (
                '生成评论'
              )}
            </button>
          </form>

          {error && (
            <div className="error-message">
              <XCircle size={20} />
              {error}
            </div>
          )}

          {result && (
            <div className="result-panel">
              <div className="result-header">
                <h2>{result.title}</h2>
                <button onClick={() => handleExport(result.id)} className="export-btn">
                  <FileDown size={18} />
                  导出CSV
                </button>
              </div>
              
              <div className="summary-section">
                <h3>新闻摘要</h3>
                <p>{result.summary}</p>
              </div>

              <div className="comments-section">
                <h3>生成的评论 ({result.comments?.length || 0}条)</h3>
                <div className="comments-grid">
                  {result.comments?.map((comment, index) => (
                    <div key={index} className="comment-card">
                      <div className="comment-meta">
                        <span className={`badge badge-style-${comment.style}`}>
                          {comment.style === 'formal' ? '正式' : comment.style === 'casual' ? '随意' : comment.style === 'humorous' ? '幽默' : comment.style === 'analytical' ? '分析' : '情感'}
                        </span>
                        <span className={`badge badge-perspective-${comment.perspective}`}>
                          {comment.perspective === 'positive' ? '积极' : comment.perspective === 'neutral' ? '中性' : '消极'}
                        </span>
                      </div>
                      <p className="comment-text">{comment.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App



