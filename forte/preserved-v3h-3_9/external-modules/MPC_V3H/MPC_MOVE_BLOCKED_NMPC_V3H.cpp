/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: MPC_MOVE_BLOCKED_NMPC_V3H
 *** Description: Additive V3H state-disturbance MPC preserving V3E envelope, delay-aware model and exporter-safe nested candidate/prediction loops
 *** Version:
***     3.9: 2026-08-26/Guilherme -  - 
 *************************************************************************/

#include "MPC_MOVE_BLOCKED_NMPC_V3H.h"
#ifdef FORTE_ENABLE_GENERATED_SOURCE_CPP
#include "MPC_MOVE_BLOCKED_NMPC_V3H_gen.cpp"
#endif


DEFINE_FIRMWARE_FB(FORTE_MPC_MOVE_BLOCKED_NMPC_V3H, g_nStringIdMPC_MOVE_BLOCKED_NMPC_V3H)

const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anDataInputNames[] = {g_nStringIdPV_RAW, g_nStringIdPV_MODEL, g_nStringIdAPPLIED_DAC, g_nStringIdENABLE_REQUEST, g_nStringIdEXTERNAL_HEALTHY, g_nStringIdRESET_REQUEST, g_nStringIdSP_RAW};

const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anDataInputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdBOOL, g_nStringIdBOOL, g_nStringIdLREAL};

const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anDataOutputNames[] = {g_nStringIdCOMMAND_ENABLE, g_nStringIdCOMMAND_DAC, g_nStringIdTRIPPED, g_nStringIdTRIP_CODE, g_nStringIdSELECTED_TARGET_DAC, g_nStringIdINPUT_BIAS_ESTIMATE_DAC, g_nStringIdPREDICTED_MAX_RAW, g_nStringIdPREDICTED_FINAL_RAW, g_nStringIdCONFIGURATION_VALID};

const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anDataOutputTypeIds[] = {g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdINT, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL};

const TDataIOID FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anEIWith[] = {0, 1, 2, 3, 4, 5, 6, 255};
const TForteInt16 FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anEIWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anEventInputNames[] = {g_nStringIdREQ};

const TDataIOID FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anEOWith[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 255};
const TForteInt16 FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anEOWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anEventOutputNames[] = {g_nStringIdCNF};


const SFBInterfaceSpec FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_stFBInterfaceSpec = {
  1, scm_anEventInputNames, scm_anEIWith, scm_anEIWithIndexes,
  1, scm_anEventOutputNames, scm_anEOWith, scm_anEOWithIndexes,
  7, scm_anDataInputNames, scm_anDataInputTypeIds,
  9, scm_anDataOutputNames, scm_anDataOutputTypeIds,
  0, nullptr
};

const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anInternalsNames[] = {g_nStringIdtrip_latched_internal, g_nStringIdtrip_code_internal, g_nStringIdhistory_count, g_nStringIdrecord_history_internal, g_nStringIdbest_found, g_nStringIdcandidate_feasible, g_nStringIdh00, g_nStringIdh01, g_nStringIdh02, g_nStringIdh03, g_nStringIdh04, g_nStringIdh05, g_nStringIdh06, g_nStringIdh07, g_nStringIdh08, g_nStringIdh09, g_nStringIdh10, g_nStringIdh11, g_nStringIdh12, g_nStringIdh13, g_nStringIdh14, g_nStringIdh15, g_nStringIdh16, g_nStringIdh17, g_nStringIdq00, g_nStringIdq01, g_nStringIdq02, g_nStringIdq03, g_nStringIdq04, g_nStringIdq05, g_nStringIdq06, g_nStringIdq07, g_nStringIdq08, g_nStringIdq09, g_nStringIdq10, g_nStringIdq11, g_nStringIdq12, g_nStringIdq13, g_nStringIdq14, g_nStringIdq15, g_nStringIdq16, g_nStringIdq17, g_nStringIdbest_cost, g_nStringIdbest_target, g_nStringIdbest_predicted_max, g_nStringIdbest_predicted_final, g_nStringIdcandidate_target, g_nStringIdpredicted_y, g_nStringIdpredicted_u, g_nStringIdprevious_u, g_nStringIddelayed_u, g_nStringIdcandidate_cost, g_nStringIdcandidate_predicted_max, g_nStringIddelta_u, g_nStringIdeffective_input, g_nStringIdphi_value, g_nStringIdtracking_error, g_nStringIdmove_value, g_nStringIdsoft_excess, g_nStringIdterminal_error, g_nStringIdcommand_candidate, g_nStringIdcandidate_index, g_nStringIdprediction_index, g_nStringIddisturbance_hat_internal, g_nStringIddisturbance_previous_pv_internal, g_nStringIddisturbance_previous_valid_internal, g_nStringIddisturbance_prediction_internal, g_nStringIddisturbance_innovation_internal};
const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_anInternalsTypeIds[] = {g_nStringIdBOOL, g_nStringIdINT, g_nStringIdDINT, g_nStringIdBOOL, g_nStringIdBOOL, g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdDINT, g_nStringIdDINT, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdLREAL};
const SInternalVarsInformation FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::scm_stInternalVars = {68, scm_anInternalsNames, scm_anInternalsTypeIds};

void FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::setInitialValues() {
  st_trip_latched_internal() = false;
  st_trip_code_internal() = 0;
  st_history_count() = 0;
  st_record_history_internal() = false;
  st_best_found() = false;
  st_candidate_feasible() = false;
  st_h00() = 0.0;
  st_h01() = 0.0;
  st_h02() = 0.0;
  st_h03() = 0.0;
  st_h04() = 0.0;
  st_h05() = 0.0;
  st_h06() = 0.0;
  st_h07() = 0.0;
  st_h08() = 0.0;
  st_h09() = 0.0;
  st_h10() = 0.0;
  st_h11() = 0.0;
  st_h12() = 0.0;
  st_h13() = 0.0;
  st_h14() = 0.0;
  st_h15() = 0.0;
  st_h16() = 0.0;
  st_h17() = 0.0;
  st_q00() = 0.0;
  st_q01() = 0.0;
  st_q02() = 0.0;
  st_q03() = 0.0;
  st_q04() = 0.0;
  st_q05() = 0.0;
  st_q06() = 0.0;
  st_q07() = 0.0;
  st_q08() = 0.0;
  st_q09() = 0.0;
  st_q10() = 0.0;
  st_q11() = 0.0;
  st_q12() = 0.0;
  st_q13() = 0.0;
  st_q14() = 0.0;
  st_q15() = 0.0;
  st_q16() = 0.0;
  st_q17() = 0.0;
  st_best_cost() = 0.0;
  st_best_target() = 0.0;
  st_best_predicted_max() = 0.0;
  st_best_predicted_final() = 0.0;
  st_candidate_target() = 0.0;
  st_predicted_y() = 0.0;
  st_predicted_u() = 0.0;
  st_previous_u() = 0.0;
  st_delayed_u() = 0.0;
  st_candidate_cost() = 0.0;
  st_candidate_predicted_max() = 0.0;
  st_delta_u() = 0.0;
  st_effective_input() = 0.0;
  st_phi_value() = 0.0;
  st_tracking_error() = 0.0;
  st_move_value() = 0.0;
  st_soft_excess() = 0.0;
  st_terminal_error() = 0.0;
  st_command_candidate() = 0.0;
  st_candidate_index() = 0;
  st_prediction_index() = 0;
  st_disturbance_hat_internal() = 0.0;
  st_disturbance_previous_pv_internal() = 0.0;
  st_disturbance_previous_valid_internal() = false;
  st_disturbance_prediction_internal() = 0.0;
  st_disturbance_innovation_internal() = 0.0;
}

void FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::alg_ALG_NMPC(void) {
  if(st_RESET_REQUEST()) {
  	st_trip_latched_internal() = false;
  	st_trip_code_internal() = 0;
  	st_disturbance_hat_internal() = 0.0;
  	st_disturbance_previous_pv_internal() = 0.0;
  	st_disturbance_previous_valid_internal() = false;
  	st_disturbance_prediction_internal() = 0.0;
  	st_disturbance_innovation_internal() = 0.0;
  }
  st_CONFIGURATION_VALID() = true;
  st_COMMAND_ENABLE() = false;
  st_COMMAND_DAC() = 0.0;
  st_SELECTED_TARGET_DAC() = 0.0;
  st_INPUT_BIAS_ESTIMATE_DAC() = 0.0;
  st_PREDICTED_MAX_RAW() = -1.0;
  st_PREDICTED_FINAL_RAW() = -1.0;
  st_record_history_internal() = ((((((st_PV_RAW() == st_PV_RAW()) && (st_PV_MODEL() == st_PV_MODEL())) && (st_APPLIED_DAC() == st_APPLIED_DAC())) && (st_SP_RAW() == st_SP_RAW())) && (st_APPLIED_DAC() >= 0.0)) && (st_APPLIED_DAC() <= 12000.0));
  if((! st_trip_latched_internal())) {
  	if((! st_ENABLE_REQUEST())) {
  		st_disturbance_hat_internal() = 0.0;
  		st_disturbance_previous_pv_internal() = 0.0;
  		st_disturbance_previous_valid_internal() = false;
  		st_disturbance_prediction_internal() = 0.0;
  		st_disturbance_innovation_internal() = 0.0;
  		st_COMMAND_ENABLE() = false;
  		st_COMMAND_DAC() = 0.0;
  	}
  	else {
  		if((! st_EXTERNAL_HEALTHY())) {
  			st_trip_latched_internal() = true;
  			st_trip_code_internal() = 2;
  		}
  		else if(((((! (st_PV_RAW() == st_PV_RAW())) || (! (st_PV_MODEL() == st_PV_MODEL()))) || (! (st_APPLIED_DAC() == st_APPLIED_DAC()))) || (! (st_SP_RAW() == st_SP_RAW())))) {
  			st_trip_latched_internal() = true;
  			st_trip_code_internal() = 1;
  		}
  		else if((((st_PV_RAW() < 0.0) || (st_PV_MODEL() < 0.0)) || (st_PV_RAW() >= 1500.0))) {
  			st_trip_latched_internal() = true;
  			st_trip_code_internal() = 3;
  		}
  		else if(((st_APPLIED_DAC() < 0.0) || (st_APPLIED_DAC() > 12000.0))) {
  			st_trip_latched_internal() = true;
  			st_trip_code_internal() = 4;
  		}
  		else if(((st_SP_RAW() < 0.0) || (st_SP_RAW() >= 800.0))) {
  			st_trip_latched_internal() = true;
  			st_trip_code_internal() = 5;
  		}
  		else if((st_history_count() < 18)) {
  			st_trip_latched_internal() = true;
  			st_trip_code_internal() = 7;
  		}
  		else {
  			if(st_disturbance_previous_valid_internal()) {
  				if((st_disturbance_previous_pv_internal() < 288.0)) {
  					st_disturbance_previous_pv_internal() = 288.0;
  				}
  				st_effective_input() = SUB(st_h00(), 11750.0);
  				if((st_effective_input() < 0.0)) {
  					st_effective_input() = 0.0;
  				}
  				else if((st_effective_input() > 500.0)) {
  					st_effective_input() = 500.0;
  				}
  				if((st_effective_input() <= 0.0)) {
  					st_phi_value() = 0.0;
  				}
  				else if((st_effective_input() <= 50.0)) {
  					st_phi_value() = ADD(0.0, MUL(2.186724147886556, SUB(st_effective_input(), 0.0)));
  				}
  				else if((st_effective_input() <= 100.0)) {
  					st_phi_value() = ADD(109.33620739432779, MUL(2.837048715132604, SUB(st_effective_input(), 50.0)));
  				}
  				else if((st_effective_input() <= 150.0)) {
  					st_phi_value() = ADD(251.18864315095797, MUL(3.148436919260821, SUB(st_effective_input(), 100.0)));
  				}
  				else if((st_effective_input() <= 200.0)) {
  					st_phi_value() = ADD(408.61048911399905, MUL(3.369389464977726, SUB(st_effective_input(), 150.0)));
  				}
  				else if((st_effective_input() <= 250.0)) {
  					st_phi_value() = ADD(577.0799623628853, MUL(3.543841594105197, SUB(st_effective_input(), 200.0)));
  				}
  				else if((st_effective_input() <= 300.0)) {
  					st_phi_value() = ADD(754.2720420681452, MUL(3.689367025828481, SUB(st_effective_input(), 250.0)));
  				}
  				else if((st_effective_input() <= 350.0)) {
  					st_phi_value() = ADD(938.7403933595692, MUL(3.814953797640478, SUB(st_effective_input(), 300.0)));
  				}
  				else if((st_effective_input() <= 400.0)) {
  					st_phi_value() = ADD(1129.4880832415931, MUL(3.925870473888026, SUB(st_effective_input(), 350.0)));
  				}
  				else if((st_effective_input() <= 450.0)) {
  					st_phi_value() = ADD(1325.7816069359944, MUL(4.025491573724398, SUB(st_effective_input(), 400.0)));
  				}
  				else if((st_effective_input() <= 500.0)) {
  					st_phi_value() = ADD(1527.0561856222143, MUL(4.116118445313023, SUB(st_effective_input(), 450.0)));
  				}
  				else {
  					st_phi_value() = 1732.8621078878655;
  				}
  				st_disturbance_prediction_internal() = ADD(ADD(288.0, MUL(0.900087626252259, SUB(st_disturbance_previous_pv_internal(), 288.0))), MUL(0.067989118863552, st_phi_value()));
  				st_disturbance_innovation_internal() = SUB(st_PV_MODEL(), st_disturbance_prediction_internal());
  				st_disturbance_hat_internal() = ADD(MUL(0.9, st_disturbance_hat_internal()), MUL(0.1, st_disturbance_innovation_internal()));
  				if((st_disturbance_hat_internal() > 100.0)) {
  					st_disturbance_hat_internal() = 100.0;
  				}
  				else if((st_disturbance_hat_internal() < -100.0)) {
  					st_disturbance_hat_internal() = -100.0;
  				}
  			}
  			st_disturbance_previous_pv_internal() = st_PV_MODEL();
  			st_disturbance_previous_valid_internal() = true;
  			st_best_found() = false;
  			st_best_cost() = 1.0E9;
  			st_best_target() = 0.0;
  			st_best_predicted_max() = -1.0;
  			st_best_predicted_final() = -1.0;
  			const auto by = 1;
  			const auto to = 12;
  			for(st_candidate_index() = 0;
  			    (by >  0 && st_candidate_index() <= to) ||
  			    (by <= 0 && st_candidate_index() >= to);
  			    st_candidate_index() = st_candidate_index() + by){
  				switch (st_candidate_index()) {
  					case 0:
  						st_candidate_target() = 0.0;
  						break;
  					case 1:
  						st_candidate_target() = 11500.0;
  						break;
  					case 2:
  						st_candidate_target() = 11550.0;
  						break;
  					case 3:
  						st_candidate_target() = 11600.0;
  						break;
  					case 4:
  						st_candidate_target() = 11650.0;
  						break;
  					case 5:
  						st_candidate_target() = 11700.0;
  						break;
  					case 6:
  						st_candidate_target() = 11750.0;
  						break;
  					case 7:
  						st_candidate_target() = 11800.0;
  						break;
  					case 8:
  						st_candidate_target() = 11845.626677302696;
  						break;
  					case 9:
  						st_candidate_target() = 11850.0;
  						break;
  					case 10:
  						st_candidate_target() = 11900.0;
  						break;
  					case 11:
  						st_candidate_target() = 11950.0;
  						break;
  					case 12:
  						st_candidate_target() = 12000.0;
  						break;
  					default:
  						st_candidate_target() = 0.0;
  						break;
  				}
  				st_q00() = st_h00();
  				st_q01() = st_h01();
  				st_q02() = st_h02();
  				st_q03() = st_h03();
  				st_q04() = st_h04();
  				st_q05() = st_h05();
  				st_q06() = st_h06();
  				st_q07() = st_h07();
  				st_q08() = st_h08();
  				st_q09() = st_h09();
  				st_q10() = st_h10();
  				st_q11() = st_h11();
  				st_q12() = st_h12();
  				st_q13() = st_h13();
  				st_q14() = st_h14();
  				st_q15() = st_h15();
  				st_q16() = st_h16();
  				st_q17() = st_h17();
  				if((st_PV_MODEL() < 288.0)) {
  					st_predicted_y() = 288.0;
  				}
  				else {
  					st_predicted_y() = st_PV_MODEL();
  				}
  				st_predicted_u() = st_APPLIED_DAC();
  				st_previous_u() = st_APPLIED_DAC();
  				st_candidate_cost() = 0.0;
  				st_candidate_predicted_max() = st_predicted_y();
  				st_candidate_feasible() = true;
  				const auto by_0 = 1;
  				const auto to_0 = 60;
  				for(st_prediction_index() = 1;
  				    (by_0 >  0 && st_prediction_index() <= to_0) ||
  				    (by_0 <= 0 && st_prediction_index() >= to_0);
  				    st_prediction_index() = st_prediction_index() + by_0){
  					if(st_candidate_feasible()) {
  						st_delta_u() = SUB(st_candidate_target(), st_predicted_u());
  						if((st_delta_u() > 750.0)) {
  							st_delta_u() = 750.0;
  						}
  						else if((st_delta_u() < -750.0)) {
  							st_delta_u() = -750.0;
  						}
  						st_predicted_u() = ADD(st_predicted_u(), st_delta_u());
  						if((st_predicted_u() > 12000.0)) {
  							st_predicted_u() = 12000.0;
  						}
  						else if((st_predicted_u() < 0.0)) {
  							st_predicted_u() = 0.0;
  						}
  						st_delayed_u() = st_q00();
  						st_q00() = st_q01();
  						st_q01() = st_q02();
  						st_q02() = st_q03();
  						st_q03() = st_q04();
  						st_q04() = st_q05();
  						st_q05() = st_q06();
  						st_q06() = st_q07();
  						st_q07() = st_q08();
  						st_q08() = st_q09();
  						st_q09() = st_q10();
  						st_q10() = st_q11();
  						st_q11() = st_q12();
  						st_q12() = st_q13();
  						st_q13() = st_q14();
  						st_q14() = st_q15();
  						st_q15() = st_q16();
  						st_q16() = st_q17();
  						st_q17() = st_predicted_u();
  						st_effective_input() = SUB(st_delayed_u(), 11750.0);
  						if((st_effective_input() < 0.0)) {
  							st_effective_input() = 0.0;
  						}
  						else if((st_effective_input() > 500.0)) {
  							st_effective_input() = 500.0;
  						}
  						if((st_effective_input() <= 0.0)) {
  							st_phi_value() = 0.0;
  						}
  						else if((st_effective_input() <= 50.0)) {
  							st_phi_value() = ADD(0.0, MUL(2.186724147886556, SUB(st_effective_input(), 0.0)));
  						}
  						else if((st_effective_input() <= 100.0)) {
  							st_phi_value() = ADD(109.33620739432779, MUL(2.837048715132604, SUB(st_effective_input(), 50.0)));
  						}
  						else if((st_effective_input() <= 150.0)) {
  							st_phi_value() = ADD(251.18864315095797, MUL(3.148436919260821, SUB(st_effective_input(), 100.0)));
  						}
  						else if((st_effective_input() <= 200.0)) {
  							st_phi_value() = ADD(408.61048911399905, MUL(3.369389464977726, SUB(st_effective_input(), 150.0)));
  						}
  						else if((st_effective_input() <= 250.0)) {
  							st_phi_value() = ADD(577.0799623628853, MUL(3.543841594105197, SUB(st_effective_input(), 200.0)));
  						}
  						else if((st_effective_input() <= 300.0)) {
  							st_phi_value() = ADD(754.2720420681452, MUL(3.689367025828481, SUB(st_effective_input(), 250.0)));
  						}
  						else if((st_effective_input() <= 350.0)) {
  							st_phi_value() = ADD(938.7403933595692, MUL(3.814953797640478, SUB(st_effective_input(), 300.0)));
  						}
  						else if((st_effective_input() <= 400.0)) {
  							st_phi_value() = ADD(1129.4880832415931, MUL(3.925870473888026, SUB(st_effective_input(), 350.0)));
  						}
  						else if((st_effective_input() <= 450.0)) {
  							st_phi_value() = ADD(1325.7816069359944, MUL(4.025491573724398, SUB(st_effective_input(), 400.0)));
  						}
  						else if((st_effective_input() <= 500.0)) {
  							st_phi_value() = ADD(1527.0561856222143, MUL(4.116118445313023, SUB(st_effective_input(), 450.0)));
  						}
  						else {
  							st_phi_value() = 1732.8621078878655;
  						}
  						st_predicted_y() = ADD(ADD(ADD(288.0, MUL(0.900087626252259, SUB(st_predicted_y(), 288.0))), MUL(0.067989118863552, st_phi_value())), st_disturbance_hat_internal());
  						if((st_predicted_y() > st_candidate_predicted_max())) {
  							st_candidate_predicted_max() = st_predicted_y();
  						}
  						if(((! (st_predicted_y() == st_predicted_y())) || (st_predicted_y() > 1400.0))) {
  							st_candidate_feasible() = false;
  						}
  						else {
  							st_tracking_error() = SUB(st_predicted_y(), st_SP_RAW());
  							st_move_value() = SUB(st_predicted_u(), st_previous_u());
  							st_candidate_cost() = ADD(ADD(st_candidate_cost(), MUL(MUL(5.0, st_tracking_error()), st_tracking_error())), MUL(MUL(4.0E-5, st_move_value()), st_move_value()));
  							if((st_predicted_y() > 1100.0)) {
  								st_soft_excess() = SUB(st_predicted_y(), 1100.0);
  								st_candidate_cost() = ADD(st_candidate_cost(), MUL(MUL(100.0, st_soft_excess()), st_soft_excess()));
  							}
  							st_previous_u() = st_predicted_u();
  						}
  					}
  				}
  				if(st_candidate_feasible()) {
  					st_terminal_error() = SUB(st_predicted_y(), st_SP_RAW());
  					st_candidate_cost() = ADD(st_candidate_cost(), MUL(MUL(10.0, st_terminal_error()), st_terminal_error()));
  					if(((! st_best_found()) || (st_candidate_cost() < st_best_cost()))) {
  						st_best_found() = true;
  						st_best_cost() = st_candidate_cost();
  						st_best_target() = st_candidate_target();
  						st_best_predicted_max() = st_candidate_predicted_max();
  						st_best_predicted_final() = st_predicted_y();
  					}
  				}
  			}
  			if((! st_best_found())) {
  				st_trip_latched_internal() = true;
  				st_trip_code_internal() = 6;
  			}
  			else {
  				st_delta_u() = SUB(st_best_target(), st_APPLIED_DAC());
  				if((st_delta_u() > 750.0)) {
  					st_delta_u() = 750.0;
  				}
  				else if((st_delta_u() < -750.0)) {
  					st_delta_u() = -750.0;
  				}
  				st_command_candidate() = ADD(st_APPLIED_DAC(), st_delta_u());
  				if((st_command_candidate() > 12000.0)) {
  					st_command_candidate() = 12000.0;
  				}
  				else if((st_command_candidate() < 0.0)) {
  					st_command_candidate() = 0.0;
  				}
  				st_COMMAND_ENABLE() = true;
  				st_COMMAND_DAC() = st_command_candidate();
  				st_SELECTED_TARGET_DAC() = st_best_target();
  				st_PREDICTED_MAX_RAW() = st_best_predicted_max();
  				st_PREDICTED_FINAL_RAW() = st_best_predicted_final();
  			}
  		}
  	}
  }
  if(st_record_history_internal()) {
  	st_h00() = st_h01();
  	st_h01() = st_h02();
  	st_h02() = st_h03();
  	st_h03() = st_h04();
  	st_h04() = st_h05();
  	st_h05() = st_h06();
  	st_h06() = st_h07();
  	st_h07() = st_h08();
  	st_h08() = st_h09();
  	st_h09() = st_h10();
  	st_h10() = st_h11();
  	st_h11() = st_h12();
  	st_h12() = st_h13();
  	st_h13() = st_h14();
  	st_h14() = st_h15();
  	st_h15() = st_h16();
  	st_h16() = st_h17();
  	st_h17() = st_APPLIED_DAC();
  	if((st_history_count() < 18)) {
  		st_history_count() = ADD(st_history_count(), 1);
  	}
  }
  st_TRIPPED() = st_trip_latched_internal();
  st_TRIP_CODE() = st_trip_code_internal();
  st_INPUT_BIAS_ESTIMATE_DAC() = 0.0;
  if(st_trip_latched_internal()) {
  	st_COMMAND_ENABLE() = false;
  	st_COMMAND_DAC() = 0.0;
  	st_SELECTED_TARGET_DAC() = 0.0;
  	st_PREDICTED_MAX_RAW() = -1.0;
  	st_PREDICTED_FINAL_RAW() = -1.0;
  }
}


void FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::enterStateSTART(void) {
  m_nECCState = scm_nStateSTART;
}

void FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::enterStateEXEC(void) {
  m_nECCState = scm_nStateEXEC;
  alg_ALG_NMPC();
  sendOutputEvent(scm_nEventCNFID);
}


void FORTE_MPC_MOVE_BLOCKED_NMPC_V3H::executeEvent(int pa_nEIID){
  bool bTransitionCleared;
  do {
    bTransitionCleared = true;
    switch(m_nECCState) {
      case scm_nStateSTART:
        if(scm_nEventREQID == pa_nEIID)
          enterStateEXEC();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      case scm_nStateEXEC:
        if(1)
          enterStateSTART();
        else
          bTransitionCleared  = false; //no transition cleared
        break;
      default:
        DEVLOG_ERROR("The state is not in the valid range! The state value is: %d. The max value can be: 2.", m_nECCState.operator TForteUInt16 ());
        m_nECCState = 0; // 0 is always the initial state
        break;
    }
    pa_nEIID = cg_nInvalidEventID; // we have to clear the event after the first check in order to ensure correct behavior
  } while(bTransitionCleared);
}


