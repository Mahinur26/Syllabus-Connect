import React, { useState, useEffect } from "react";
import { Snackbar, Alert } from "@mui/material";

//Chaged the api url to accept both the local host and deployed url
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";


function App() {
 //The const variables handle the state manegment of key info- ensuring that the ui reflects the variables accurately
 const [user, setUser] = useState(null);
 const [email, setEmail] = useState("");
 const [password, setPassword] = useState("");
 const [isLogin, setIsLogin] = useState(true);
 const [activeTab, setActiveTab] = useState("inventory");


 const [syllabi, setSyllabi] = useState([]);
 const [selectedSyllabus, setSelectedSyllabus] = useState("");
 const [syllabusItems, setSyllabusItems] = useState([]);
 const [uploadedFile, setUploadedFile] = useState(null);
 const [filePreview, setFilePreview] = useState(null);
 const [extractedText, setExtractedText] = useState("");

 // Alert state (for general notifications)
 const [alertState, setAlertState] = useState({
   open: false,
   message: '',
   severity: 'info' // 'error' | 'warning' | 'info' | 'success'
 });

 const [chatMessages, setChatMessages] = useState([]);
 const [chatInput, setChatInput] = useState("");
 const [loading, setLoading] = useState(false);


 useEffect(() => {
   const stored = localStorage.getItem("bullavor_user");
   if (stored) setUser(JSON.parse(stored));
 }, []);


 useEffect(() => {
   //fetch syllabi when user logs in
   if (user) fetchSyllabi();
 }, [user]);

 // Helper function to show alerts
 const showAlert = (message, severity = 'info') => {
   setAlertState({ open: true, message, severity });
 };

 // Helper function to close alerts
 const handleAlertClose = (event, reason) => {
   if (reason === 'clickaway') return;
   setAlertState({ ...alertState, open: false });
 };

 //Sends a POST request to the backend to either log in or sign up the user based on the isLogin state
 //A POST request means sending data from the frontend to the backend for processing, in this case for logging/signing in
 const handleAuth = async () => {
   setLoading(true);
   try {
     const res = await fetch(
       `${API_URL}/auth/${isLogin ? "login" : "signup"}`,
       {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ email, password }),
       }
     );
     const data = await res.json();
     //If the response is successful, sets the user to both state and local storage
     if (res.ok) {
       setUser(data.user);
       localStorage.setItem("bullavor_user", JSON.stringify(data.user));
       showAlert(isLogin ? 'Welcome back!' : 'Account created successfully!', 'success');
     } else {
       showAlert(data.detail || 'Authentication failed', 'error');
     }
   } catch (err) {
     showAlert('Error: ' + err.message, 'error');
   }
   setLoading(false);
 };


 //function that fetches the syllabi of the user that is currently logged in
 const fetchSyllabi = async () => {
   try {
     const res = await fetch(`${API_URL}/syllabi/${user.uid}`);
     if (res.ok) {
       const data = await res.json();
       // Ensure data is an array
       setSyllabi(Array.isArray(data) ? data : []);
     } else {
       // If endpoint doesn't exist or returns error, set to empty array
       setSyllabi([]);
     }
   } catch (err) {
     console.error(err);
     // On error, ensure syllabi is still an array
     setSyllabi([]);
   }
 };

 //function that fetches the items from a selected syllabus
 const fetchSyllabusItems = async (syllabusId) => {
   try {
     const res = await fetch(`${API_URL}/syllabi/${syllabusId}/items`);
     const data = await res.json();
     // Initialize items with selected property
     setSyllabusItems(data.map(item => ({ ...item, selected: item.selected || false })));
   } catch (err) {
     console.error(err);
   }
 };


 // Handle file upload
 const handleFileUpload = async (event) => {
   const file = event.target.files[0];
   if (!file) return;

   setUploadedFile(file);
   setFilePreview(URL.createObjectURL(file));
   setLoading(true);

   try {
    // First try to extract text from the PDF so we can show it in the UI
    try {
      const extractForm = new FormData();
      extractForm.append('file', file);

      const extractRes = await fetch(`${API_URL}/pdf/extract`, {
        method: 'POST',
        body: extractForm,
      });
      const extractData = await extractRes.json();
      if (extractRes.ok) {
        setExtractedText(extractData.text || "");
      } else {
        // Extraction failed; warn but continue with upload
        showAlert(extractData.detail || 'PDF extraction failed', 'warning');
      }
    } catch (err) {
      console.error('PDF extraction error', err);
      showAlert('PDF extraction error', 'warning');
    }

    // Continue with existing syllabus upload behavior
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', user.uid);

    const res = await fetch(`${API_URL}/syllabi/upload`, {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();
    if (res.ok) {
      await fetchSyllabi();
      showAlert('Syllabus uploaded successfully!', 'success');
    } else {
      showAlert(data.detail || 'Upload failed', 'error');
    }
   } catch (err) {
     showAlert('Error uploading file', 'error');
   }
   setLoading(false);
 };

  // Re-run extraction for the currently selected file
  const reExtract = async () => {
    if (!uploadedFile) return;
    setLoading(true);
    try {
      const extractForm = new FormData();
      extractForm.append('file', uploadedFile);

      const extractRes = await fetch(`${API_URL}/pdf/extract`, {
        method: 'POST',
        body: extractForm,
      });
      const extractData = await extractRes.json();
      if (extractRes.ok) {
        setExtractedText(extractData.text || "");
        showAlert('Re-extraction complete', 'success');
      } else {
        showAlert(extractData.detail || 'Re-extraction failed', 'error');
      }
    } catch (err) {
      console.error('Re-extract error', err);
      showAlert('Re-extraction error', 'error');
    }
    setLoading(false);
  };

  const downloadExtractedText = () => {
    const text = extractedText || '';
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = (uploadedFile && uploadedFile.name ? uploadedFile.name.replace(/\.pdf$/i, '') : 'extracted') + '.txt';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

 // Handle syllabus selection
 useEffect(() => {
   if (selectedSyllabus) {
     fetchSyllabusItems(selectedSyllabus);
   } else {
     setSyllabusItems([]);
   }
 }, [selectedSyllabus]);


 // Add items to Google Calendar
 const addToGoogleCalendar = async () => {
   if (!selectedSyllabus || syllabusItems.length === 0) {
     showAlert("Please select a syllabus with items", "warning");
     return;
   }

   setLoading(true);
   try {
     const res = await fetch(`${API_URL}/calendar/add`, {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify({
         user_id: user.uid,
         syllabus_id: selectedSyllabus,
         items: syllabusItems.filter(item => item.selected),
       }),
     });

     const data = await res.json();
     if (res.ok) {
       showAlert("Items added to Google Calendar successfully!", "success");
     } else {
       showAlert(data.detail || "Failed to add to calendar", "error");
     }
   } catch (err) {
     showAlert("Error adding to calendar", "error");
   }
   setLoading(false);
 };

 // Group syllabus items by category
 const groupSyllabusItemsByCategory = (items) => {
   const grouped = {};
   const categoryOrder = [
     "Exams",
     "Assignments",
     "Homework",
     "Projects",
     "Tests",
     "Quizzes",
     "Essays",
     "Other",
   ];

   items.forEach((item) => {
     const category = item.category || "Other";
     if (!grouped[category]) {
       grouped[category] = [];
     }
     grouped[category].push(item);
   });

   // Sort categories according to predefined order
   const sorted = {};
   categoryOrder.forEach((cat) => {
     if (grouped[cat]) {
       sorted[cat] = grouped[cat];
     }
   });

   // Add any categories not in the predefined list
   Object.keys(grouped).forEach((cat) => {
     if (!categoryOrder.includes(cat)) {
       sorted[cat] = grouped[cat];
     }
   });

   return sorted;
 };

 // Toggle item selection
 const toggleItemSelection = (itemId) => {
   setSyllabusItems(items =>
     items.map(item =>
       item.id === itemId ? { ...item, selected: !item.selected } : item
     )
   );
 };

 // Parse recipe response into structured sections
 const parseRecipeResponse = (text) => {
   const sections = {
     dishName: '',
     ingredients: [],
     instructions: [],
     rawText: text
   };
   
   // Extract dish name
   const dishMatch = text.match(/DISH NAME:\s*(.+?)(?=\n|INGREDIENTS:|$)/i);
   if (dishMatch) sections.dishName = dishMatch[1].trim();
   
   // Extract ingredients
   const ingredientsMatch = text.match(/INGREDIENTS:\s*([\s\S]+?)(?=INSTRUCTIONS:|$)/i);
   if (ingredientsMatch) {
     sections.ingredients = ingredientsMatch[1]
       .split('\n')
       .filter(line => line.trim().startsWith('-'))
       .map(line => line.trim().substring(1).trim());
   }
   
   // Extract instructions
   const instructionsMatch = text.match(/INSTRUCTIONS:\s*([\s\S]+?)$/i);
   if (instructionsMatch) {
     sections.instructions = instructionsMatch[1]
       .split('\n')
       .filter(line => /^\d+\./.test(line.trim()))
       .map(line => line.trim());
   }
   
   return sections;
 };

 //Used to send the user's message to the ai model in the backend and return the response in the chat UI
 const sendMessage = async () => {
   if (!chatInput.trim()) return;


   setChatMessages([...chatMessages, { role: "user", content: chatInput }]);
   const msg = chatInput;
   setChatInput("");
   setLoading(true);


   try {
     const res = await fetch(`${API_URL}/chat`, {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify({ user_id: user.uid, message: msg }),
     });
     const data = await res.json();
     setChatMessages((prev) => [
       ...prev,
       { role: "assistant", content: data.response },
     ]);
   } catch (err) {
     setChatMessages((prev) => [
       ...prev,
       { role: "assistant", content: "Error occurred" },
     ]);
     showAlert("Chat error occurred", "error");
   }
   setLoading(false);
 };


//The main return statement that renders the UI based on whether the user is logged in or not
return (
  <>
    {/* Unified Alert System - Always rendered */}
    <Snackbar
      open={alertState.open}
      autoHideDuration={6000}
      onClose={handleAlertClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
    >
      <Alert
        onClose={handleAlertClose}
        severity={alertState.severity}
        variant="filled"
        sx={{ width: '100%' }}
      >
        {alertState.message}
      </Alert>
    </Snackbar>

    {!user ? (
      <div className="min-h-screen flex items-center justify-center p-6" style={{ backgroundColor: '#8686AC' }}>
  <div className="bg-[#D3D3D3] rounded-2xl shadow-2xl p-10 w-full max-w-md">
          <h1 className="text-4xl font-extrabold mb-8 text-center" style={{ color: '#505081' }}>Syllabus Connect</h1>
          <div className="space-y-5">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAuth()}
              className="w-full px-5 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#505081] transition"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAuth()}
              className="w-full px-5 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#505081] transition"
            />
            <button
              onClick={handleAuth}
              disabled={loading}
              className="w-full text-white py-3 rounded-xl transition font-semibold disabled:opacity-50"
              style={{ backgroundColor: '#505081' }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#272757'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#505081'}
            >
              {loading ? 'Loading...' : (isLogin ? 'Login' : 'Sign Up')}
            </button>
          </div>
          <p className="text-center mt-6">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="hover:underline font-medium"
              style={{ color: '#505081' }}
            >
              {isLogin ? 'Need an account? Sign up' : 'Have an account? Login'}
            </button>
          </p>
        </div>
      </div>
    ) : (
      <div className="min-h-screen" style={{ backgroundColor: '#8686AC' }}>
        {/* Header */}
  <header className="bg-[#D3D3D3] shadow-md">
          <div className="max-w-6xl mx-auto px-6 py-5 flex justify-between items-center">
            <h1 className="text-3xl font-bold" style={{ color: '#505081' }}>Syllabus Connect</h1>
            <div className="flex gap-6 items-center">
              <span className="text-sm text-gray-600 font-medium">{user.email}</span>
              <button
                onClick={() => {
                  setUser(null);
                  localStorage.removeItem('bullavor_user');
                }}
                className="text-sm text-red-600 hover:underline font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
          {/* Tabs */}
          <div className="flex gap-3">
            <button
                onClick={() => setActiveTab('inventory')}
              className={`px-6 py-2 rounded-full font-semibold transition ${
                activeTab === 'inventory' 
                  ? 'text-white shadow-lg' 
                  : 'bg-[#D3D3D3] border hover:bg-[#8686AC] hover:bg-opacity-30'
              }`}
              style={activeTab === 'inventory' ? { backgroundColor: '#505081' } : {}}
            >
              Syllabus
            </button>
            <button
                onClick={() => setActiveTab('chat')}
              className={`px-6 py-2 rounded-full font-semibold transition ${
                activeTab === 'chat' 
                  ? 'text-white shadow-lg' 
                  : 'bg-[#D3D3D3] border hover:bg-[#8686AC] hover:bg-opacity-30'
              }`}
              style={activeTab === 'chat' ? { backgroundColor: '#505081' } : {}}
            >
              Syllabus Buddy
            </button>
          </div>

          {/* Syllabus Tab */}
          {activeTab === 'inventory' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Panel - Upload Area */}
          <div className="space-y-6">
            <div className="bg-[#D3D3D3] rounded-2xl shadow-lg p-6">
              <label
                htmlFor="file-upload"
                className="flex flex-col items-center justify-center w-full h-96 border-2 border-dashed rounded-xl cursor-pointer transition hover:bg-opacity-50"
                style={{ 
                  borderColor: '#505081',
                  backgroundColor: filePreview ? 'rgba(134, 134, 172, 0.1)' : 'rgba(134, 134, 172, 0.05)'
                }}
              >
                {filePreview ? (
                  <div className="w-full h-full flex flex-col items-center justify-center p-4">
                    <div className="text-4xl mb-4" style={{ color: '#505081' }}>📄</div>
                    <p className="text-sm font-medium mb-2" style={{ color: '#505081' }}>
                      {uploadedFile?.name || 'Syllabus Preview'}
                    </p>
                    <p className="text-xs text-gray-500">Click to upload a different file</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center">
                    <svg
                      className="w-16 h-16 mb-4"
                      style={{ color: '#505081' }}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                    <p className="text-lg font-semibold mb-2" style={{ color: '#505081' }}>
                      Upload
                    </p>
                  </div>
                )}
                <input
                  id="file-upload"
                  type="file"
                  className="hidden"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileUpload}
                  disabled={loading}
                />
              </label>
            </div>
            {/* Extracted text preview + actions */}
            {uploadedFile && (
              <div className="bg-[#D3D3D3] rounded-2xl shadow-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-semibold text-gray-800">Selected file:</div>
                  <div className="text-sm text-gray-600">{uploadedFile.name}</div>
                </div>
                <label className="block text-sm font-semibold mb-2 text-gray-700">Extracted text preview</label>
                <textarea
                  readOnly
                  value={extractedText}
                  rows={8}
                  className="w-full p-3 rounded-lg border resize-none bg-white text-sm"
                />
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => navigator.clipboard.writeText(extractedText || '')}
                    disabled={!extractedText}
                    className="px-4 py-2 rounded-lg text-white"
                    style={{ backgroundColor: '#505081' }}
                  >
                    Copy text
                  </button>
                  <button
                    onClick={() => {
                      setUploadedFile(null);
                      setFilePreview(null);
                      setExtractedText("");
                    }}
                    className="px-4 py-2 rounded-lg border"
                  >
                    Clear
                  </button>
                </div>

                <div className="mt-4 border-t pt-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm text-gray-600">Words: {extractedText ? extractedText.trim().split(/\s+/).filter(Boolean).length : 0}</div>
                    <div className="text-sm text-gray-600">Chars: {extractedText ? extractedText.length : 0}</div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={reExtract}
                      disabled={!uploadedFile || loading}
                      className="px-4 py-2 rounded-lg text-white"
                      style={{ backgroundColor: '#505081' }}
                    >
                      {loading ? 'Working...' : 'Re-extract'}
                    </button>
                    <button
                      onClick={downloadExtractedText}
                      disabled={!extractedText}
                      className="px-4 py-2 rounded-lg border"
                    >
                      Download text
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Syllabus Selection and Items */}
          <div className="space-y-6">
            {/* Syllabus Selection Dropdown */}
            <div className="bg-[#D3D3D3] rounded-2xl shadow-lg p-6">
              <label className="block text-sm font-semibold mb-2 text-gray-700">
                Syllabus Selection
              </label>
              <select
                value={selectedSyllabus}
                onChange={(e) => setSelectedSyllabus(e.target.value)}
                className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#505081] bg-white transition"
              >
                <option value="">Select a syllabus</option>
                {Array.isArray(syllabi) && syllabi.map((syllabus) => (
                  <option key={syllabus.id} value={syllabus.id}>
                    {syllabus.name}
                  </option>
                ))}
              </select>
          
            </div>

            {/* Syllabus Items List */}
            <div className="bg-[#D3D3D3] rounded-2xl shadow-lg p-6 space-y-4">
              <h2 className="text-xl font-bold mb-4">Syllabus Items</h2>
              {!selectedSyllabus ? (
                <p className="text-gray-500 text-center py-8">
                  Select a syllabus to view items
                </p>
              ) : syllabusItems.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No items found</p>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {Object.entries(groupSyllabusItemsByCategory(syllabusItems)).map(
                    ([category, items]) => (
                      <div key={category}>
                        <h3 className="text-lg font-semibold text-gray-800 mb-2">
                          {category} ({items.length})
                        </h3>
                        <div className="space-y-2">
                          {items.map((item) => (
                            <div
                              key={item.id}
                              className={`p-4 rounded-xl border flex items-start gap-3 shadow-sm cursor-pointer transition ${
                                item.selected
                                  ? 'border-2'
                                  : 'border'
                              }`}
                              style={{
                                backgroundColor: item.selected
                                  ? 'rgba(80, 80, 129, 0.1)'
                                  : 'rgba(134, 134, 172, 0.15)',
                                borderColor: item.selected ? '#505081' : 'rgba(0, 0, 0, 0.1)',
                              }}
                              onClick={() => toggleItemSelection(item.id)}
                            >
                              <input
                                type="checkbox"
                                checked={item.selected || false}
                                onChange={() => toggleItemSelection(item.id)}
                                className="mt-1"
                                style={{ accentColor: '#505081' }}
                              />
                              <div className="flex-1">
                                <div className="font-semibold text-gray-800">
                                  {item.assignment || item.name}
                                </div>
                                {item.due_date && (
                                  <div className="text-sm text-gray-600 mt-1">
                                    Due: {new Date(item.due_date).toLocaleDateString()}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  )}
                </div>
              )}
            </div>

            {/* Add to Google Calendar Button */}
            <button
              onClick={addToGoogleCalendar}
              disabled={loading || !selectedSyllabus || syllabusItems.filter(item => item.selected).length === 0}
              className="w-full text-white py-3 rounded-xl transition font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#505081' }}
              onMouseEnter={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#272757')}
              onMouseLeave={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#505081')}
            >
              {loading ? 'Loading...' : 'Add to Google Calendar'}
            </button>
          </div>
        </div>
      )}

      {/* Chat Tab */}
      {activeTab === 'chat' && (
  <div className="bg-[#D3D3D3] rounded-2xl shadow-lg p-6 space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Syllabus Buddy</h2>
            <select
              value={selectedSyllabus}
              onChange={(e) => setSelectedSyllabus(e.target.value)}
              className="w-1/4 px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#505081] bg-white transition"
            >
              <option value="">Select a syllabus</option>
              {Array.isArray(syllabi) && syllabi.map((syllabus) => (
                <option key={syllabus.id} value={syllabus.id}>
                  {syllabus.name}
                </option>
              ))}
            </select>
          </div>

          <div className="h-96 overflow-y-auto p-4 bg-gray-50 rounded-xl space-y-3">
            {chatMessages.length === 0 ? (
              <p className="text-gray-500 text-center">Ask me about your syllabus!</p>
            ) : (
              chatMessages.map((msg, i) => (
                <div key={i} className={`${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                  <div 
                    className={`inline-block p-4 rounded-xl ${
                      msg.role === 'user' ? 'text-white max-w-xs' : 'bg-gray-200 max-w-2xl'
                    }`}
                    style={msg.role === 'user' ? { backgroundColor: '#505081' } : {}}
                  >
                    {msg.role === 'assistant' ? (
                      (() => {
                        const recipe = parseRecipeResponse(msg.content);
                        // If we found structured sections, render them nicely
                        if (recipe.dishName || recipe.ingredients.length > 0 || recipe.instructions.length > 0) {
                          return (
                            <div className="text-gray-800">
                              {recipe.dishName && (
                                <h3 className="font-bold text-lg mb-3" style={{ color: '#505081' }}>{recipe.dishName}</h3>
                              )}
                              {recipe.ingredients.length > 0 && (
                                <div className="mb-4">
                                  <h4 className="font-semibold mb-2 text-gray-700">Ingredients:</h4>
                                  <ul className="space-y-1">
                                    {recipe.ingredients.map((ing, idx) => (
                                      <li key={idx} className="text-sm flex items-start">
                                        <span className="mr-2" style={{ color: '#505081' }}>•</span>
                                        <span>{ing}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {recipe.instructions.length > 0 && (
                                <div>
                                  <h4 className="font-semibold mb-2 text-gray-700">Instructions:</h4>
                                  <ol className="space-y-2">
                                    {recipe.instructions.map((step, idx) => (
                                      <li key={idx} className="text-sm flex items-start">
                                        <span className="font-semibold mr-2 min-w-[1.5rem]" style={{ color: '#505081' }}>
                                          {idx + 1}.
                                        </span>
                                        <span>{step.replace(/^\d+\.\s*/, '')}</span>
                                      </li>
                                    ))}
                                  </ol>
                                </div>
                              )}
                            </div>
                          );
                        } else {
                          // Fallback to plain text if no structure found
                          return <div className="text-sm whitespace-pre-wrap">{msg.content}</div>;
                        }
                      })()
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Ask anything..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              className="flex-1 px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#505081] transition"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading}
              className="px-6 py-3 text-white rounded-xl transition font-semibold disabled:opacity-50"
              style={{ backgroundColor: '#505081' }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#272757'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#505081'}
            >
              {loading ? '...' : 'Send'}
            </button>
          </div>
        </div>
          )}
        </main>
      </div>
    )}
  </>
);
}


export default App;