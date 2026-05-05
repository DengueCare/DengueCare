export class Patient {
    constructor({ id, nome, iniciais, idade, telefone, dias, riscoBadge, riscoTexto, grupoAtual, statusBox, comorbidades, scoreAtual, trend, trendColor, labelsGrafico, dadosGrafico, historico }) {
        this.id = id;
        this.nome = nome;
        this.iniciais = iniciais;
        this.idade = idade;
        this.telefone = telefone;
        this.dias = dias;
        this.riscoBadge = riscoBadge;
        this.riscoTexto = riscoTexto;
        this.grupoAtual = grupoAtual;
        this.statusBox = statusBox;
        this.comorbidades = comorbidades || [];
        this.scoreAtual = scoreAtual;
        this.trend = trend;
        this.trendColor = trendColor;
        this.labelsGrafico = labelsGrafico || [];
        this.dadosGrafico = dadosGrafico || [];
        this.historico = historico || [];
    }
}
