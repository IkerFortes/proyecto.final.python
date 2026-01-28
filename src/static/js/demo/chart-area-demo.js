// Configuraciones globales
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';


function number_format(number, decimals, dec_point, thousands_sep) {
    number = (number + '').replace(',', '').replace(' ', '');
    var n = !isFinite(+number) ? 0 : + number,
        prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
        sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
        dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
        s = '',
        toFixedFix = function(n, prec) {
            var k = Math.pow(10, prec);
            return '' + Math.round(n * k) / k;
        };
    s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
    if (s[0].length > 3) {
        s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
    }
    if ((s[1] || '').length < prec) {
        s[1] = s[1] || '';
        s[1] += new Array(prec - s[1].length + 1).join('0');
    }
    return s.join(dec);
}

// ------------------------------------------------------------------------------------------ FUNCIONES NECESARIAS ------------------------- //

// VARIABLE GLOBAL PARA EL GRÁFICO
var myLineChart = null;

// FUNCIÓN PARA CARGAR DATOS DESDE FLASK
function actualizarGrafico(rango) {
    fetch(`/api/grafico/${rango}`)
        .then(response => response.json())
        .then(remoteData => {
            const canvas = document.getElementById("myAreaChart");
            const msg = document.getElementById("no-data-message");

            // VALIDACIÓN: ¿Hay datos reales?
            // Verificamos si el array está vacío o si la suma de sus valores es 0
            const tieneDatos = remoteData.values && remoteData.values.length > 0 && remoteData.values.some(v => v > 0);

            if (!tieneDatos) {
                // Si no hay datos: ocultamos canvas y mostramos mensaje
                canvas.style.display = "none";
                msg.style.display = "block";
                if (myLineChart) myLineChart.destroy();
                return; // Cortamos la ejecución aquí
            } else {
                // Si hay datos: mostramos canvas y ocultamos mensaje
                canvas.style.display = "block";
                msg.style.display = "none";
            }

            var ctx = document.getElementById("myAreaChart");

            // Si el gráfico ya existe, se destruye para evitar solapamientos
            if (myLineChart) {
                myLineChart.destroy();
            }

            // CREACIÓN DEL GRÁFICO CON TUS ESTILOS ORIGINALES
            myLineChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: remoteData.labels, // Datos de Flask
                    datasets: [{
                        label: "Saldo",
                        lineTension: 0.3,
                        backgroundColor: "rgba(78, 115, 223, 0.05)",
                        borderColor: "rgba(78, 115, 223, 1)",
                        pointRadius: 3,
                        pointBackgroundColor: "rgba(78, 115, 223, 1)",
                        pointBorderColor: "rgba(78, 115, 223, 1)",
                        pointHoverRadius: 3,
                        pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
                        pointHoverBorderColor: "rgba(78, 115, 223, 1)",
                        pointHitRadius: 10,
                        pointBorderWidth: 2,
                        data: remoteData.values, // Datos de Flask
                    }],
                },
                options: {
                    maintainAspectRatio: false,
                    layout: { padding: { left: 10, right: 25, top: 25, bottom: 0 } },
                    scales: {
                        xAxes: [{
                            time: { unit: 'date' },
                            gridLines: { display: false, drawBorder: false },
                            ticks: { maxTicksLimit: 7 }
                        }],
                        yAxes: [{
                            ticks: {
                                maxTicksLimit: 5,
                                padding: 10,
                                callback: function(value) { return number_format(value) + '€'; }
                            },
                            gridLines: {
                                color: "rgb(234, 236, 244)",
                                zeroLineColor: "rgb(234, 236, 244)",
                                drawBorder: false,
                                borderDash: [2],
                                zeroLineBorderDash: [2]
                            }
                        }],
                    },
                    legend: { display: false },
                    tooltips: {
                        backgroundColor: "rgb(255,255,255)",
                        bodyFontColor: "#858796",
                        titleMarginBottom: 10,
                        titleFontColor: '#6e707e',
                        titleFontSize: 14,
                        borderColor: '#dddfeb',
                        borderWidth: 1,
                        xPadding: 15,
                        yPadding: 15,
                        displayColors: false,
                        intersect: false,
                        mode: 'index',
                        caretPadding: 10,
                        callbacks: {
                            label: function(tooltipItem, chart) {
                                var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
                                return datasetLabel + ': ' + number_format(tooltipItem.yLabel) + '€';
                            }
                        }
                    }
                }
            });
        });
}

// Carga inicial al abrir la página
document.addEventListener("DOMContentLoaded", function() {
    actualizarGrafico('mensual');
});