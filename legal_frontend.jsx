import React, { useState, useEffect } from 'react';
import { Upload, Search, FileText, Zap, BarChart3, AlertCircle } from 'lucide-react';

const LegalResearchApp = () => {
  const [currentTab, setCurrentTab] = useState('home');
  const [cases, setCases] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [similarCases, setSimilarCases] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState('');
  const [chatResponse, setChatResponse] = useState('');

  const API_BASE = 'http://localhost:8000';

  // Load cases on mount
  useEffect(() => {
    loadCases();
    loadStats();
  }, []);

  const loadCases = async () => {
    try {
      const response = await fetch(`${API_BASE}/cases`);
      const data = await response.json();
      setCases(data.cases || []);
    } catch (error) {
      console.error('Error loading cases:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      
      if (response.ok) {
        alert(`Case ${data.case_id} uploaded successfully!`);
        loadCases();
        loadStats();
      } else {
        alert('Error uploading file: ' + data.detail);
      }
    } catch (error) {
      alert('Error uploading file: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, top_k: 5 }),
      });
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error('Error searching:', error);
      alert('Error searching cases');
    } finally {
      setLoading(false);
    }
  };

  const handleFindSimilar = async (caseId) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/similar/${caseId}`);
      const data = await response.json();
      setSimilarCases(data.similar_cases || []);
      setSelectedCase(caseId);
    } catch (error) {
      console.error('Error finding similar cases:', error);
      alert('Error finding similar cases');
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim() || !selectedCase) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: selectedCase, question }),
      });
      const data = await response.json();
      setChatResponse(data.answer || 'No answer found');
    } catch (error) {
      console.error('Error asking question:', error);
      alert('Error processing question');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navigation */}
      <nav className="bg-white shadow-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-8 h-8 text-indigo-600" />
            <h1 className="text-2xl font-bold text-gray-800">Legal Research AI</h1>
          </div>
          <div className="flex gap-4">
            {['home', 'search', 'upload', 'analytics'].map((tab) => (
              <button
                key={tab}
                onClick={() => setCurrentTab(tab)}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  currentTab === tab
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* HOME TAB */}
        {currentTab === 'home' && (
          <div className="space-y-8">
            {/* Hero Section */}
            <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
              <Zap className="w-16 h-16 mx-auto mb-4 text-indigo-600" />
              <h2 className="text-4xl font-bold text-gray-800 mb-4">
                AI-Powered Legal Research Platform
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Find relevant case laws, analyze similarities, and discover precedents with AI
              </p>
              <div className="flex gap-4 justify-center flex-wrap">
                <button
                  onClick={() => setCurrentTab('upload')}
                  className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-bold hover:bg-indigo-700 transition"
                >
                  Upload Documents
                </button>
                <button
                  onClick={() => setCurrentTab('search')}
                  className="bg-white text-indigo-600 border-2 border-indigo-600 px-8 py-3 rounded-lg font-bold hover:bg-indigo-50 transition"
                >
                  Search Cases
                </button>
              </div>
            </div>

            {/* Stats Grid */}
            {stats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard
                  label="Total Cases"
                  value={stats.total_cases}
                  icon="📚"
                />
                <StatCard
                  label="Citations Found"
                  value={stats.total_citations}
                  icon="🔗"
                />
                <StatCard
                  label="Legal Areas"
                  value={stats.unique_legal_areas}
                  icon="⚖️"
                />
                <StatCard
                  label="Searches"
                  value={stats.total_searches}
                  icon="🔍"
                />
              </div>
            )}

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <FeatureCard
                icon={<Upload className="w-12 h-12" />}
                title="Document Upload"
                description="Upload PDF documents of legal judgments and case files"
              />
              <FeatureCard
                icon={<Search className="w-12 h-12" />}
                title="Semantic Search"
                description="AI-powered search that understands legal meaning and context"
              />
              <FeatureCard
                icon={<BarChart3 className="w-12 h-12" />}
                title="Case Similarity"
                description="Automatically find similar cases and relevant precedents"
              />
            </div>

            {/* Recent Cases */}
            {cases.length > 0 && (
              <div className="bg-white rounded-xl shadow-md p-6">
                <h3 className="text-2xl font-bold text-gray-800 mb-4">Recent Cases</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b">
                      <tr>
                        <th className="text-left py-2 px-4">Case ID</th>
                        <th className="text-left py-2 px-4">Title</th>
                        <th className="text-left py-2 px-4">Court</th>
                        <th className="text-left py-2 px-4">Legal Area</th>
                        <th className="text-left py-2 px-4">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cases.slice(0, 5).map((caseItem) => (
                        <tr key={caseItem.case_id} className="border-b hover:bg-gray-50">
                          <td className="py-2 px-4 font-mono text-sm">{caseItem.case_id}</td>
                          <td className="py-2 px-4">{caseItem.title}</td>
                          <td className="py-2 px-4">{caseItem.court}</td>
                          <td className="py-2 px-4">
                            <span className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded">
                              {caseItem.legal_area}
                            </span>
                          </td>
                          <td className="py-2 px-4">
                            <button
                              onClick={() => handleFindSimilar(caseItem.case_id)}
                              className="text-indigo-600 hover:text-indigo-800 font-medium"
                            >
                              Find Similar
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* UPLOAD TAB */}
        {currentTab === 'upload' && (
          <div className="bg-white rounded-xl shadow-lg p-12">
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Upload Legal Documents</h2>
            
            <div className="border-4 border-dashed border-indigo-300 rounded-lg p-12 text-center">
              <Upload className="w-16 h-16 mx-auto mb-4 text-indigo-600" />
              <h3 className="text-xl font-bold text-gray-800 mb-2">Upload PDF Documents</h3>
              <p className="text-gray-600 mb-6">
                Upload judgment PDFs to extract and analyze legal content
              </p>
              <label className="inline-block">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="hidden"
                />
                <span className={`inline-block bg-indigo-600 text-white px-8 py-3 rounded-lg font-bold cursor-pointer hover:bg-indigo-700 transition ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                  {uploading ? 'Uploading...' : 'Choose PDF File'}
                </span>
              </label>
            </div>

            {cases.length > 0 && (
              <div className="mt-12">
                <h3 className="text-2xl font-bold text-gray-800 mb-4">All Uploaded Cases</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {cases.map((caseItem) => (
                    <div key={caseItem.case_id} className="bg-gray-50 p-4 rounded-lg border-l-4 border-indigo-600">
                      <h4 className="font-bold text-gray-800">{caseItem.title}</h4>
                      <p className="text-sm text-gray-600">ID: {caseItem.case_id}</p>
                      <p className="text-sm text-gray-600">Court: {caseItem.court}</p>
                      <p className="text-sm text-gray-600">Legal Area: {caseItem.legal_area}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* SEARCH TAB */}
        {currentTab === 'search' && (
          <div className="space-y-8">
            {/* Search Box */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-3xl font-bold text-gray-800 mb-6">Semantic Search</h2>
              <div className="flex gap-4">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Search for cases by legal concept, party name, or topic..."
                  className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-indigo-600"
                />
                <button
                  onClick={handleSearch}
                  disabled={loading}
                  className={`bg-indigo-600 text-white px-8 py-3 rounded-lg font-bold hover:bg-indigo-700 transition ${loading ? 'opacity-50' : ''}`}
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-4">
                  Results ({searchResults.length})
                </h3>
                <div className="space-y-4">
                  {searchResults.map((result, idx) => (
                    <div
                      key={idx}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                      onClick={() => handleFindSimilar(result.case_id)}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-gray-800">{result.title}</h4>
                        <span className="bg-green-100 text-green-800 px-3 py-1 rounded text-sm">
                          {(result.similarity_score * 100).toFixed(1)}% match
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{result.preview}...</p>
                      <div className="flex gap-4 text-xs text-gray-500">
                        <span>🏛️ {result.court}</span>
                        <span>📜 {result.legal_area}</span>
                        <span>📅 {result.judgment_date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Similar Cases */}
            {selectedCase && similarCases.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-4">Similar Cases</h3>
                <div className="space-y-3">
                  {similarCases.map((similar, idx) => (
                    <div key={idx} className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-bold text-gray-800">{similar.title}</h4>
                          <p className="text-sm text-gray-600">{similar.court}</p>
                        </div>
                        <span className="bg-blue-200 text-blue-800 px-3 py-1 rounded text-sm">
                          {(similar.similarity_score * 100).toFixed(1)}% similar
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Q&A Section */}
                <div className="mt-8 border-t pt-8">
                  <h4 className="text-xl font-bold text-gray-800 mb-4">Ask About Case</h4>
                  <div className="space-y-4">
                    <input
                      type="text"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="Ask a question about this case..."
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-indigo-600"
                    />
                    <button
                      onClick={handleAskQuestion}
                      disabled={loading}
                      className="w-full bg-indigo-600 text-white px-4 py-3 rounded-lg font-bold hover:bg-indigo-700 transition"
                    >
                      {loading ? 'Processing...' : 'Get Answer'}
                    </button>
                    {chatResponse && (
                      <div className="bg-green-50 border-l-4 border-green-600 p-4 rounded">
                        <h5 className="font-bold text-green-800 mb-2">Answer:</h5>
                        <p className="text-gray-700">{chatResponse}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ANALYTICS TAB */}
        {currentTab === 'analytics' && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-3xl font-bold text-gray-800 mb-8">Platform Analytics</h2>
            {stats ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <AnalyticsCard label="Total Cases in System" value={stats.total_cases} />
                <AnalyticsCard label="Total Citations Found" value={stats.total_citations} />
                <AnalyticsCard label="Unique Legal Areas" value={stats.unique_legal_areas} />
                <AnalyticsCard label="Search Queries" value={stats.total_searches} />
              </div>
            ) : (
              <p className="text-gray-600">Loading analytics...</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const StatCard = ({ label, value, icon }) => (
  <div className="bg-white rounded-lg shadow-md p-6 text-center">
    <div className="text-4xl mb-2">{icon}</div>
    <p className="text-gray-600 text-sm mb-2">{label}</p>
    <p className="text-4xl font-bold text-indigo-600">{value}</p>
  </div>
);

const FeatureCard = ({ icon, title, description }) => (
  <div className="bg-white rounded-lg shadow-md p-6">
    <div className="text-indigo-600 mb-4">{icon}</div>
    <h3 className="text-xl font-bold text-gray-800 mb-2">{title}</h3>
    <p className="text-gray-600">{description}</p>
  </div>
);

const AnalyticsCard = ({ label, value }) => (
  <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg p-8 border-l-4 border-indigo-600">
    <p className="text-gray-600 text-sm mb-2">{label}</p>
    <p className="text-5xl font-bold text-indigo-600">{value}</p>
  </div>
);

export default LegalResearchApp;
