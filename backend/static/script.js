// Initialize mouse position for gradient effect
let mouseX = window.innerWidth / 2;
let mouseY = window.innerHeight / 2;
let targetX = mouseX;
let targetY = mouseY;
const ease = 0.1;

// Smoothly update gradient position on mouse move
function updateMousePosition(e) {
    targetX = e.clientX;
    targetY = e.clientY;
}

// Smooth animation loop
function animate() {
    // Ease the values
    const dx = targetX - mouseX;
    const dy = targetY - mouseY;
    
    if (Math.abs(dx) > 0.1 || Math.abs(dy) > 0.1) {
        mouseX += dx * ease;
        mouseY += dy * ease;
        
        // Update CSS variables
        document.documentElement.style.setProperty('--mouse-x', `${mouseX}px`);
        document.documentElement.style.setProperty('--mouse-y', `${mouseY}px`);
    }
    
    requestAnimationFrame(animate);
}

// Start animation loop
requestAnimationFrame(animate);

// Add event listeners for mouse movement
if (!/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
    // Only add mousemove for non-touch devices
    window.addEventListener('mousemove', updateMousePosition);
    window.addEventListener('scroll', updateMousePosition);
}

// Handle touch events for mobile
document.addEventListener('touchmove', (e) => {
    const touch = e.touches[0];
    targetX = touch.clientX;
    targetY = touch.clientY;
    e.preventDefault();
}, { passive: false });

// Update gradient position on window resize
window.addEventListener('resize', () => {
    mouseX = window.innerWidth / 2;
    mouseY = window.innerHeight / 2;
    targetX = mouseX;
    targetY = mouseY;
});

// Create floating particles
function createParticles() {
    const particlesContainer = document.createElement('div');
    particlesContainer.className = 'particles-container';
    document.body.appendChild(particlesContainer);
    
    for (let i = 0; i < 15; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        const size = Math.random() * 8 + 3;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        particle.style.opacity = Math.random() * 0.5 + 0.1;
        particle.style.animationDuration = `${Math.random() * 30 + 20}s`;
        particle.style.animationDelay = `-${Math.random() * 10}s`;
        particlesContainer.appendChild(particle);
    }
}

// Sample prescription data
const SAMPLE_PRESCRIPTION = 'Patient: John Doe\nAge: 45\n\nMedications:\n1. Metformin 500mg - 1 tab twice daily\n2. Amlodipine 5mg - 1 tab daily\n3. Atorvastatin 20mg - 1 tab at night\n\nAllergies: Penicillin\n\nNotes: Patient has type 2 diabetes and hypertension.';

// UI Helper Functions
function showLoading(message = 'Analyzing your prescription...') {
    console.log('showLoading called with message:', message);
    const loadingDiv = document.getElementById('loading');
    const loadingText = loadingDiv ? loadingDiv.querySelector('.loading-text') : null;
    
    if (loadingDiv && loadingText) {
        loadingText.textContent = message;
        loadingDiv.classList.add('visible');
        document.body.style.overflow = 'hidden'; // Prevent scrolling when loading
        console.log('Loading spinner is now visible');
    } else {
        console.error('Loading elements not found');
    }
}

function hideLoading() {
    console.log('hideLoading called');
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) {
        loadingDiv.classList.remove('visible');
        document.body.style.overflow = ''; // Re-enable scrolling
        // Reset the loading text after animation completes
        setTimeout(() => {
            const loadingText = loadingDiv.querySelector('.loading-text');
            if (loadingText) {
                loadingText.textContent = 'Analyzing your prescription...';
            }
        }, 500);
    } else {
        console.error('Loading div not found');
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    if (!errorDiv) {
        console.error('Error div not found');
        return;
    }
    
    // Create error message with icon
    errorDiv.innerHTML = `
        <div class="error-content">
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
        </div>
        <button class="error-close" aria-label="Close error">&times;</button>
    `;
    
    // Show error with animation
    errorDiv.style.display = 'flex';
    errorDiv.style.opacity = '0';
    errorDiv.style.transform = 'translateY(-20px)';
    
    // Trigger reflow and animate in
    void errorDiv.offsetWidth;
    errorDiv.style.opacity = '1';
    errorDiv.style.transform = 'translateY(0)';
    
    // Scroll to error if not in view
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Add close button handler
    const closeBtn = errorDiv.querySelector('.error-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            hideError();
        });
    }
    
    // Auto-hide error after 10 seconds
    const autoHideTimer = setTimeout(hideError, 10000);
    
    // Clear timer if user interacts with the error
    errorDiv.addEventListener('mouseenter', () => clearTimeout(autoHideTimer));
    errorDiv.addEventListener('click', () => clearTimeout(autoHideTimer));
}

function hideError() {
    const errorDiv = document.getElementById('error');
    if (errorDiv && errorDiv.style.display !== 'none') {
        errorDiv.style.opacity = '0';
        errorDiv.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 300);
    }
}

// Main application initialization
document.addEventListener('DOMContentLoaded', () => {
    // Initialize DOM elements
    const prescriptionInput = document.getElementById('prescription');
    const analyzeBtn = document.getElementById('analyze-btn');
    const sampleBtn = document.getElementById('sample-btn');
    const downloadBtn = document.getElementById('download-btn');
    const newAnalysisBtn = document.getElementById('new-analysis-btn');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const loadingDiv = document.getElementById('loading');
    const loadingText = loadingDiv ? loadingDiv.querySelector('.loading-text') : null;
    
    let analysisData = []; // Store analysis results for PDF download
    
    // Initialize particles and gradient
    createParticles();
    document.documentElement.style.setProperty('--mouse-x', `${mouseX}px`);
    document.documentElement.style.setProperty('--mouse-y', `${mouseY}px`);
    
    // Event Listeners
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzePrescription);
    }
    
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadPdf);
    }
    
    if (newAnalysisBtn) {
        newAnalysisBtn.addEventListener('click', resetForm);
    }
    
    if (sampleBtn) {
        sampleBtn.addEventListener('click', loadSamplePrescription);
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+Enter to analyze
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            analyzePrescription();
        }
        
        // Escape to clear input
        if (e.key === 'Escape') {
            if (prescriptionInput && document.activeElement === prescriptionInput) {
                prescriptionInput.value = '';
            }
        }
    });
    
    // Log initialization
    console.log('RxGuardian initialized');
    
    // Core application functions
    async function analyzePrescription() {
        console.log('Starting analysis...');
        const resultsSection = document.getElementById('results');
        
        if (!prescriptionInput) {
            console.error('Prescription input element not found');
            return;
        }
        
        // Hide any previous results and errors
        if (resultsSection) {
            resultsSection.style.opacity = '0';
            resultsSection.style.visibility = 'hidden';
        }
        
        hideError(); // Hide any previous errors
        
        const prescriptionText = prescriptionInput.value.trim();
        console.log('Prescription text:', prescriptionText);
        
        if (!prescriptionText) {
            const errorMsg = 'Please enter a prescription to analyze.';
            console.warn(errorMsg);
            showError(errorMsg);
            prescriptionInput.focus();
            return;
        }
        
        // Show loading spinner before making the API call
        showLoading('Analyzing your prescription...');
        
        try {
            const requestBody = { prescription: prescriptionText };
            console.log('Sending request to /analyze with body:', requestBody);
            
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            console.log('Received response status:', response.status);
            
            // Check if the response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response:', text);
                throw new Error('Received invalid response from server. Please try again.');
            }
            
            const data = await response.json().catch(error => {
                console.error('Failed to parse JSON:', error);
                throw new Error('Could not process the server response.');
            });
            
            console.log('Received analysis data:', data);
            
            if (!response.ok) {
                throw new Error(data.error || `Server responded with status ${response.status}`);
            }
            
            if (!data.analysis || data.analysis.length === 0) {
                throw new Error('No medications could be analyzed from the provided prescription.');
            }
            
            analysisData = data.analysis;
            console.log('Analysis data set, showing results...');
            showResults(analysisData);
            
        } catch (error) {
            console.error('Analysis error:', error);
            showError(error.message || 'An error occurred while analyzing the prescription.');
        } finally {
            console.log('Hiding loading indicator');
            hideLoading();
        }
    }

    function showResults(analysis) {
        console.log('showResults called with analysis:', analysis);
        const contentDiv = document.getElementById('analysis-content');
        const resultsSection = document.getElementById('results');
        
        if (!contentDiv || !resultsSection) {
            console.error('Required elements not found:', { contentDiv, resultsSection });
            return;
        }
        
        contentDiv.innerHTML = '';
        
        // Check if there's an error in the analysis
        if (analysis.length === 1 && analysis[0].medication_name === 'Error') {
            const errorMessage = analysis[0].reasoning || 'An error occurred during analysis';
            console.error('Analysis error:', errorMessage);
            showError(errorMessage);
            return;
        }
        
        if (analysis && analysis.length > 0) {
            // Make sure results section is visible
            resultsSection.style.display = 'block';
            resultsSection.style.opacity = '1';
            resultsSection.style.visibility = 'visible';
            analysis.forEach((med, index) => {
                console.log(`Processing medication ${index + 1}:`, med);
                const row = document.createElement('tr');
                
                // Medication name and basic info
                const medCell = document.createElement('td');
                medCell.className = 'med-cell';
                
                const medName = document.createElement('div');
                medName.className = 'medication-name';
                medName.innerHTML = `
                    <i class="fas fa-pills"></i>
                    <strong>${med.medication_name || 'Unknown Medication'}</strong>
                `;
                
                const medDetails = document.createElement('div');
                medDetails.className = 'medication-details';
                if (med.generic_name) {
                    const genericEl = document.createElement('div');
                    genericEl.innerHTML = `<i class="fas fa-tag"></i> ${med.generic_name}`;
                    medDetails.appendChild(genericEl);
                }
                if (med.manufacturer) {
                    const mfrEl = document.createElement('div');
                    mfrEl.innerHTML = `<i class="fas fa-industry"></i> ${med.manufacturer}`;
                    medDetails.appendChild(mfrEl);
                }
                
                medCell.appendChild(medName);
                medCell.appendChild(medDetails);
                
                // Dosage and frequency
                const detailsCell = document.createElement('td');
                detailsCell.className = 'details-cell';
                
                const doseRow = document.createElement('div');
                doseRow.className = 'detail-row';
                doseRow.innerHTML = `
                    <i class="fas fa-syringe"></i>
                    <span>${med.prescribed_dose || 'Dose not specified'}</span>
                `;
                
                const freqRow = document.createElement('div');
                freqRow.className = 'detail-row';
                freqRow.innerHTML = `
                    <i class="far fa-clock"></i>
                    <span>${med.frequency || 'Frequency not specified'}</span>
                `;
                
                detailsCell.appendChild(doseRow);
                detailsCell.appendChild(freqRow);
                
                if (med.duration) {
                    const durationRow = document.createElement('div');
                    durationRow.className = 'detail-row';
                    durationRow.innerHTML = `
                        <i class="far fa-calendar-alt"></i>
                        <span>${med.duration}</span>
                    `;
                    detailsCell.appendChild(durationRow);
                }
                
                if (med.prescribed_cost) {
                    const costRow = document.createElement('div');
                    costRow.className = 'detail-row cost';
                    costRow.innerHTML = `
                        <i class="fas fa-tag"></i>
                        <span>Cost: ₹${med.prescribed_cost}</span>
                    `;
                    detailsCell.appendChild(costRow);
                }
                
                // Recommendations and alternatives
                const recCell = document.createElement('td');
                recCell.className = 'rec-cell';
                
                if (med.overdose) {
                    const warningDiv = document.createElement('div');
                    warningDiv.className = 'alert alert-warning';
                    warningDiv.innerHTML = `
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>Potential Overdose:</strong> ${med.reasoning || 'No specific reasoning provided.'}
                    `;
                    recCell.appendChild(warningDiv);
                }
                
                if (med.cheaper_alternatives && med.cheaper_alternatives.length > 0) {
                    const altDiv = document.createElement('div');
                    altDiv.className = 'alternatives';
                    
                    const altHeader = document.createElement('div');
                    altHeader.className = 'alternatives-header';
                    altHeader.innerHTML = `
                        <i class="fas fa-money-bill-wave"></i>
                        <strong>Cheaper Alternatives:</strong>
                    `;
                    
                    const altList = document.createElement('ul');
                    med.cheaper_alternatives.forEach(alt => {
                        const li = document.createElement('li');
                        const nameDiv = document.createElement('div');
                        nameDiv.className = 'alt-name';
                        nameDiv.textContent = alt.name;
                        
                        const priceDiv = document.createElement('div');
                        priceDiv.className = 'alt-price';
                        priceDiv.textContent = `₹${alt.cost}`;
                        
                        li.appendChild(nameDiv);
                        li.appendChild(priceDiv);
                        
                        if (alt.reason) {
                            const reasonDiv = document.createElement('div');
                            reasonDiv.className = 'alt-reason';
                            reasonDiv.textContent = alt.reason;
                            li.appendChild(reasonDiv);
                        }
                        
                        altList.appendChild(li);
                    });
                    
                    altDiv.appendChild(altHeader);
                    altDiv.appendChild(altList);
                    recCell.appendChild(altDiv);
                }
                
                if (med.recommendations && med.recommendations.length > 0) {
                    const recDiv = document.createElement('div');
                    recDiv.className = 'recommendations';
                    
                    const recHeader = document.createElement('div');
                    recHeader.className = 'recommendations-header';
                    recHeader.innerHTML = `
                        <i class="fas fa-lightbulb"></i>
                        <strong>Recommendations:</strong>
                    `;
                    
                    const recList = document.createElement('ul');
                    med.recommendations.forEach(rec => {
                        const li = document.createElement('li');
                        li.textContent = rec;
                        recList.appendChild(li);
                    });
                    
                    recDiv.appendChild(recHeader);
                    recDiv.appendChild(recList);
                    recCell.appendChild(recDiv);
                }
                
                if (recCell.children.length === 0) {
                    const noRec = document.createElement('span');
                    noRec.className = 'text-muted';
                    noRec.textContent = 'No specific recommendations available.';
                    recCell.appendChild(noRec);
                }
                
                // Add cells to row
                row.appendChild(medCell);
                row.appendChild(detailsCell);
                row.appendChild(recCell);
                contentDiv.appendChild(row);
            });
            
            // Show results section with animation
            if (resultsDiv) {
                resultsDiv.classList.remove('hidden');
                resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        } else {
            showError('No medications could be analyzed from the provided prescription.');
        }
    }
    
    async function downloadPdf() {
        if (!analysisData || analysisData.length === 0) {
            showError('No analysis data available to download.');
            return;
        }
        
        showLoading('Preparing your report...');
        
        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ analysis: analysisData })
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate PDF');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `RxGuardian_Report_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
        } catch (error) {
            console.error('Download error:', error);
            showError('Failed to download the report. Please try again.');
        } finally {
            hideLoading();
        }
    }

    function loadSamplePrescription() {
        prescriptionInput.value = SAMPLE_PRESCRIPTION;
        prescriptionInput.focus();
        // Auto-scroll to input
        setTimeout(() => {
            prescriptionInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    }

    function resetForm() {
        prescriptionInput.value = '';
        resultsDiv.classList.add('hidden');
        errorDiv.classList.add('hidden');
        prescriptionInput.focus();
    }

    function showError(message) {
        const errorDiv = document.getElementById('error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 10000);
    }

    function showLoading(message = 'Loading...') {
        const loadingDiv = document.getElementById('loading');
        loadingDiv.textContent = message;
        loadingDiv.classList.remove('hidden');
    }

    function hideLoading() {
        const loadingDiv = document.getElementById('loading');
        loadingDiv.classList.add('hidden');
    }

    // Initialize particles and gradient
    createParticles();
    document.documentElement.style.setProperty('--mouse-x', `${mouseX}px`);
    document.documentElement.style.setProperty('--mouse-y', `${mouseY}px`);
    
    // Set up keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+Enter to analyze
        if (e.ctrlKey && e.key === 'Enter' && document.activeElement === prescriptionInput) {
            e.preventDefault();
            analyzePrescription();
        }
        // Escape to clear input
        if (e.key === 'Escape' && document.activeElement === prescriptionInput) {
            prescriptionInput.value = '';
        }
    });

    // Focus the input field when the page loads
    if (prescriptionInput) {
        prescriptionInput.focus();
    }

    // Add animation class to header on load
    const header = document.querySelector('header');
    if (header) {
        setTimeout(() => {
            header.classList.add('animate__animated', 'animate__fadeInDown');
        }, 300);
    }
});