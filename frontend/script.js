

document.addEventListener('DOMContentLoaded', () => {
  const researchBtn = document.getElementById('researchBtn');
  const companyInput = document.getElementById('companyInput');
  const timelineSteps = document.querySelectorAll('.step');
  const scoreDisplay = document.getElementById('scoreDisplay');
  const scoreValue = document.getElementById('scoreValue');
  const swotGrid = document.getElementById('swotGrid');
  const reportCard = document.getElementById('reportCard');
  const warningSection = document.getElementById('warningSection');
  const reportContent = document.getElementById('reportContent');
  let jobId = null;
  let isProcessing = false;

  const stepOrder = ['research', 'analysis', 'writing', 'critique'];

  function updateTimeline(jobStep) {
    if (jobStep === 'done') {
      timelineSteps.forEach(step => step.classList.add('done'));
      scoreDisplay.style.display = 'block';
      swotGrid.style.display = 'grid';
      reportCard.style.display = 'block';
      researchBtn.disabled = false;
      researchBtn.textContent = 'Research';
      isProcessing = false;
    } else if (jobStep === 'failed') {
      timelineSteps.forEach(step => step.classList.remove('done'));
      scoreDisplay.style.display = 'none';
      swotGrid.style.display = 'none';
      reportCard.style.display = 'none';
      warningSection.style.display = 'none';
      researchBtn.disabled = false;
      researchBtn.textContent = 'Research';
      isProcessing = false;
      reportContent.innerHTML = '<p style="color: var(--accent-primary);">Error: Analysis failed. Please try again.</p>';
      reportCard.style.display = 'block';
    } else if (jobStep) {
      const currentIndex = stepOrder.indexOf(jobStep.toLowerCase());
      timelineSteps.forEach((step, i) => {
        if (currentIndex >= 0 && i <= currentIndex) {
          step.classList.add('active');
        } else {
          step.classList.remove('active');
        }
      });
    }
  }

  function renderMarkdown(text) {
    if (!text) return '';
    return text
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/\n/g, '<br>');
  }

  function renderSWOT(data) {
    if (!data) return;
    const strengthsHtml = (data.strengths || []).map(item => `<li>${item}</li>`).join('');
    const weaknessesHtml = (data.weaknesses || []).map(item => `<li>${item}</li>`).join('');
    const opportunitiesHtml = (data.opportunities || []).map(item => `<li>${item}</li>`).join('');
    const threatsHtml = (data.threats || []).map(item => `<li>${item}</li>`).join('');

    swotGrid.innerHTML = `
      <div class="swot-cell strengths">
        <h3>Strengths</h3>
        <ul>${strengthsHtml || '<li>No strengths identified</li>'}</ul>
      </div>
      <div class="swot-cell weaknesses">
        <h3>Weaknesses</h3>
        <ul>${weaknessesHtml || '<li>No weaknesses identified</li>'}</ul>
      </div>
      <div class="swot-cell opportunities">
        <h3>Opportunities</h3>
        <ul>${opportunitiesHtml || '<li>No opportunities identified</li>'}</ul>
      </div>
      <div class="swot-cell threats">
        <h3>Threats</h3>
        <ul>${threatsHtml || '<li>No threats identified</li>'}</ul>
      </div>
    `;
  }

  function renderWarning(gapDetails) {
    if (!gapDetails || (Array.isArray(gapDetails) && gapDetails.length === 0)) {
      warningSection.style.display = 'none';
      return;
    }
    const items = Array.isArray(gapDetails) ? gapDetails : [gapDetails];
    const itemsHtml = items.map(item => `<li>${item}</li>`).join('');
    warningSection.innerHTML = `<h3>Unverified Claims</h3><ul>${itemsHtml}</ul>`;
    warningSection.style.display = 'block';
  }

  researchBtn.addEventListener('click', async () => {
    const companyName = companyInput.value.trim();
    if (!companyName || isProcessing) return;

    isProcessing = true;
    researchBtn.disabled = true;
    researchBtn.textContent = 'Processing...';
    timelineSteps.forEach(step => step.classList.remove('done', 'active'));
    scoreDisplay.style.display = 'none';
    swotGrid.style.display = 'none';
    reportCard.style.display = 'none';
    warningSection.style.display = 'none';

    try {
      const postResp = await fetch('https://market-research-agent-ekvl.onrender.com/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_name: companyName })
      });

      const data = await postResp.json();
      jobId = data.job_id;

      if (!jobId) {
        alert('Failed to start research');
        isProcessing = false;
        researchBtn.disabled = false;
        researchBtn.textContent = 'Research';
        return;
      }

      pollStatus();
    } catch (err) {
      console.error('Research request failed:', err);
      isProcessing = false;
      researchBtn.disabled = false;
      researchBtn.textContent = 'Research';
    }
  });

  function pollStatus() {
    if (!jobId) return;
    const interval = setInterval(async () => {
      try {
        const resp = await fetch(`https://market-research-agent-ekvl.onrender.com/status/${jobId}`);
        const data = await resp.json();

        updateTimeline(data.step);

        if (data.step === 'done') {
          clearInterval(interval);

          const reportResp = await fetch(`https://market-research-agent-ekvl.onrender.com/report/${jobId}`);
          const reportData = await reportResp.json();

          if (reportData.report) {
            reportContent.innerHTML = renderMarkdown(reportData.report);
          }

          if (reportData.opportunity_score !== undefined && reportData.opportunity_score !== null) {
            scoreValue.textContent = `${reportData.opportunity_score}/10`;
          }

          if (reportData.swot) {
            renderSWOT(reportData.swot);
          }

          renderWarning(reportData.gap_details);

        } else if (data.step === 'failed') {
          clearInterval(interval);
          updateTimeline('failed');
        }
      } catch (err) {
        console.error('Status poll failed:', err);
      }
    }, 2000);
  }
});

