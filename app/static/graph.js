// Set today's date
document.getElementById('today-date').innerText = new Date().toLocaleDateString();

// get each elements
const ctx_weekly = document.getElementById('weekly-chart').getContext('2d');
const ctx_all = document.getElementById('all-chart').getContext('2d');

fetch('http://127.0.0.1:5001/weekly_feeling.json')
    .then(response => response.json())
    .then(data => {
        const week_emoji = data.emoji
        const week_numbers = data.numbers
        const week_backgroundColor = data.backgroundColor
        const week_borderColor = data.borderColor

        createChart(ctx_weekly, week_emoji, week_numbers, week_backgroundColor, week_borderColor);
    })
    .catch(error => console.error('Error emoji chart:', error))

fetch('http://127.0.0.1:5001/all_feeling.json')
    .then(response => response.json())
    .then(data => {
        const all_emoji = data.emoji
        const all_numbers = data.numbers
        const all_backgroundColor = data.backgroundColor
        const all_borderColor = data.borderColor

        createChart(ctx_all, all_emoji, all_numbers, all_backgroundColor, all_borderColor);
    })
    .catch(error => console.error('Error emoji chart:', error))


function createChart(ctx, emoji, numbers, backgroundColor, borderColor) {
    new Chart(ctx, {
        type: 'doughnut', // Specify chart type
        data: {
            labels: emoji, // Labels for chart segments
            datasets: [{
                label: 'My feeling',
                data: numbers, // Values for each segment
                backgroundColor: backgroundColor,
                borderColor: borderColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            legend: {
                position: 'top',
            },
            plugins: {
                legend: {
                    labels: {
                        font: {
                            size: 25
                        }
                    }
                }
            }
        },
        plugins: [doughnutLabel]
    })
}

const doughnutLabel = {
    id: 'doughnutLabel',
    beforeDatasetsDraw(chart, args, pluginOptions) {
        const { ctx, data } = chart;

        ctx.save()
        chart.canvas.parentNode.style.height = '350px';
        chart.canvas.parentNode.style.width = '350px';
        const xCoor = chart.getDatasetMeta(0).data[0].x;
        const yCoor = chart.getDatasetMeta(0).data[0].y + 7;
        ctx.font = '60px san-serif';
        ctx.textAlign = 'center';
        ctx.textBaseLine = 'middle';
        ctx.fillText(data.labels[0], xCoor, yCoor);
    }
}
