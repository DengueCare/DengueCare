export class GetPatientsUseCase {
    constructor(patientRepository) {
        this.patientRepository = patientRepository;
    }

    async execute() {
        return await this.patientRepository.getAllPatients();
    }
}

export class GetPatientByIdUseCase {
    constructor(patientRepository) {
        this.patientRepository = patientRepository;
    }

    async execute(id) {
        return await this.patientRepository.getPatientById(id);
    }
}
