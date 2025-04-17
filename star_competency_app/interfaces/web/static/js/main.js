// star_competency_app/interfaces/web/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert.alert-success, .alert.alert-info');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Add STAR component expansion functionality
    document.querySelectorAll('.star-expand-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var targetId = this.getAttribute('data-target');
            var targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.classList.toggle('d-none');
                if (targetElement.classList.contains('d-none')) {
                    this.textContent = 'Show More';
                } else {
                    this.textContent = 'Show Less';
                }
            }
        });
    });
});

// Function to evaluate a STAR story
function evaluateStarStory(storyId) {
    if (!confirm('Would you like to evaluate this STAR story using AI?')) {
        return;
    }
    
    const evaluationContainer = document.getElementById('evaluation-container');
    const loadingIndicator = document.getElementById('evaluation-loading');
    
    if (evaluationContainer && loadingIndicator) {
        evaluationContainer.classList.add('d-none');
        loadingIndicator.classList.remove('d-none');
        
        fetch(`/star/${storyId}/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        })
        .then(response => response.json())
        .then(data => {
            loadingIndicator.classList.add('d-none');
            evaluationContainer.classList.remove('d-none');
            
            if (data.error) {
                evaluationContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            let evaluationHtml = `<div class="ai-feedback">${data.evaluation}</div>`;
            
            if (data.scores) {
                evaluationHtml += '<div class="mt-4"><h5>Scores:</h5><div>';
                for (const [category, score] of Object.entries(data.scores)) {
                    let badgeClass = 'bg-secondary';
                    if (score >= 4.5) badgeClass = 'bg-success';
                    else if (score >= 3.5) badgeClass = 'bg-primary';
                    else if (score >= 2.5) badgeClass = 'bg-info';
                    else if (score >= 1.5) badgeClass = 'bg-warning';
                    else badgeClass = 'bg-danger';
                    
                    evaluationHtml += `<span class="score-badge badge ${badgeClass}">${category}: ${score}</span>`;
                }
                evaluationHtml += '</div></div>';
            }
            
            evaluationContainer.innerHTML = evaluationHtml;
        })
        .catch(error => {
            loadingIndicator.classList.add('d-none');
            evaluationContainer.classList.remove('d-none');
            evaluationContainer.innerHTML = `<div class="alert alert-danger">An error occurred: ${error.message}</div>`;
            console.error('Error:', error);
        });
    }
}

// Function to analyze a case study
function analyzeCaseStudy(caseId) {
    if (!confirm('Would you like to analyze this case study using AI?')) {
        return;
    }
    
    const queryInput = document.getElementById('analysis-query');
    const query = queryInput ? queryInput.value : 'Analyze this case study';
    
    const analysisContainer = document.getElementById('analysis-container');
    const loadingIndicator = document.getElementById('analysis-loading');
    
    if (analysisContainer && loadingIndicator) {
        analysisContainer.classList.add('d-none');
        loadingIndicator.classList.remove('d-none');
        
        const formData = new FormData();
        formData.append('query', query);
        
        fetch(`/case-study/${caseId}/analyze`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        })
        .then(response => response.json())
        .then(data => {
            loadingIndicator.classList.add('d-none');
            analysisContainer.classList.remove('d-none');
            
            if (data.error) {
                analysisContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            let analysisHtml = `<div class="ai-feedback">${data.analysis}</div>`;
            
            if (data.competency_alignment && Object.keys(data.competency_alignment).length > 0) {
                analysisHtml += '<div class="mt-4"><h5>Competency Alignment:</h5><ul>';
                for (const [competency, info] of Object.entries(data.competency_alignment)) {
                    const relevanceClass = info.relevant ? 'text-success' : 'text-muted';
                    analysisHtml += `<li class="${relevanceClass}"><strong>${competency}</strong> - Mentions: ${info.mentions}</li>`;
                }
                analysisHtml += '</ul></div>';
            }
            
            analysisContainer.innerHTML = analysisHtml;
        })
        .catch(error => {
            loadingIndicator.classList.add('d-none');
            analysisContainer.classList.remove('d-none');
            analysisContainer.innerHTML = `<div class="alert alert-danger">An error occurred: ${error.message}</div>`;
            console.error('Error:', error);
        });
    }
}