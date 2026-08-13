/*************************************************************************
 *** FORTE Library Element
 ***
 *** This file was generated using the 4DIAC FORTE Export Filter V1.0.x NG!
 ***
 *** Name: MPC_MOVE_BLOCKED_NMPC_V1
 *** Description: Fail-closed move-blocked nonlinear MPC reference for the first raw-count commissioning envelope
 *** Version:
***     1.0: 2026-08-10/Guilherme -  - 
 *************************************************************************/

#include "MPC_MOVE_BLOCKED_NMPC_V1.h"
#ifdef FORTE_ENABLE_GENERATED_SOURCE_CPP
#include "MPC_MOVE_BLOCKED_NMPC_V1_gen.cpp"
#endif


DEFINE_FIRMWARE_FB(FORTE_MPC_MOVE_BLOCKED_NMPC_V1, g_nStringIdMPC_MOVE_BLOCKED_NMPC_V1)

const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anDataInputNames[] = {g_nStringIdPV_RAW, g_nStringIdPV_MODEL, g_nStringIdAPPLIED_DAC, g_nStringIdENABLE_REQUEST, g_nStringIdEXTERNAL_HEALTHY, g_nStringIdRESET_REQUEST, g_nStringIdSP_RAW};

const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anDataInputTypeIds[] = {g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdBOOL, g_nStringIdBOOL, g_nStringIdLREAL};

const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anDataOutputNames[] = {g_nStringIdCOMMAND_ENABLE, g_nStringIdCOMMAND_DAC, g_nStringIdTRIPPED, g_nStringIdTRIP_CODE, g_nStringIdSELECTED_TARGET_DAC, g_nStringIdINPUT_BIAS_ESTIMATE_DAC, g_nStringIdPREDICTED_MAX_RAW, g_nStringIdPREDICTED_FINAL_RAW, g_nStringIdCONFIGURATION_VALID};

const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anDataOutputTypeIds[] = {g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdINT, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL};

const TDataIOID FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anEIWith[] = {0, 1, 2, 3, 4, 5, 6, 255};
const TForteInt16 FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anEIWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anEventInputNames[] = {g_nStringIdREQ};

const TDataIOID FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anEOWith[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 255};
const TForteInt16 FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anEOWithIndexes[] = {0};
const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anEventOutputNames[] = {g_nStringIdCNF};


const SFBInterfaceSpec FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_stFBInterfaceSpec = {
  1, scm_anEventInputNames, scm_anEIWith, scm_anEIWithIndexes,
  1, scm_anEventOutputNames, scm_anEOWith, scm_anEOWithIndexes,
  7, scm_anDataInputNames, scm_anDataInputTypeIds,
  9, scm_anDataOutputNames, scm_anDataOutputTypeIds,
  0, nullptr
};

const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anInternalsNames[] = {g_nStringIdtrip_latched_internal, g_nStringIdtrip_code_internal, g_nStringIdinput_bias_internal, g_nStringIdprevious_prediction_internal, g_nStringIdprevious_applied_internal, g_nStringIdprevious_valid_internal, g_nStringIdresidual, g_nStringIdeffective_input, g_nStringIdeffective_model_u, g_nStringIdphi_value, g_nStringIdphi_slope, g_nStringIdsensitivity, g_nStringIdbias_update, g_nStringIdbest_found, g_nStringIdbest_cost, g_nStringIdbest_target, g_nStringIdbest_predicted_max, g_nStringIdbest_predicted_final, g_nStringIdcandidate_target, g_nStringIdpredicted_y, g_nStringIdpredicted_u, g_nStringIdprevious_u, g_nStringIdcandidate_cost, g_nStringIdcandidate_predicted_max, g_nStringIdcandidate_feasible, g_nStringIddelta_u, g_nStringIdtracking_error, g_nStringIdmove_value, g_nStringIdsoft_excess, g_nStringIdterminal_error, g_nStringIdcommand_candidate, g_nStringIdcandidate_index, g_nStringIdprediction_index};
const CStringDictionary::TStringId FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_anInternalsTypeIds[] = {g_nStringIdBOOL, g_nStringIdINT, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdBOOL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdLREAL, g_nStringIdDINT, g_nStringIdDINT};
const SInternalVarsInformation FORTE_MPC_MOVE_BLOCKED_NMPC_V1::scm_stInternalVars = {33, scm_anInternalsNames, scm_anInternalsTypeIds};

void FORTE_MPC_MOVE_BLOCKED_NMPC_V1::setInitialValues() {
  st_trip_latched_internal() = false;
  st_trip_code_internal() = 0;
  st_input_bias_internal() = 0.0;
  st_previous_prediction_internal() = 0.0;
  st_previous_applied_internal() = 0.0;
  st_previous_valid_internal() = false;
  st_residual() = 0.0;
  st_effective_input() = 0.0;
  st_effective_model_u() = 0.0;
  st_phi_value() = 0.0;
  st_phi_slope() = 0.0;
  st_sensitivity() = 0.0;
  st_bias_update() = 0.0;
  st_best_found() = false;
  st_best_cost() = 0.0;
  st_best_target() = 0.0;
  st_best_predicted_max() = 0.0;
  st_best_predicted_final() = 0.0;
  st_candidate_target() = 0.0;
  st_predicted_y() = 0.0;
  st_predicted_u() = 0.0;
  st_previous_u() = 0.0;
  st_candidate_cost() = 0.0;
  st_candidate_predicted_max() = 0.0;
  st_candidate_feasible() = false;
  st_delta_u() = 0.0;
  st_tracking_error() = 0.0;
  st_move_value() = 0.0;
  st_soft_excess() = 0.0;
  st_terminal_error() = 0.0;
  st_command_candidate() = 0.0;
  st_candidate_index() = 0;
  st_prediction_index() = 0;
}

void FORTE_MPC_MOVE_BLOCKED_NMPC_V1::alg_ALG_NMPC(void) {
  st_CONFIGURATION_VALID() = true;
  if(st_RESET_REQUEST()) {
  	st_trip_latched_internal() = false;
  	st_trip_code_internal() = 0;
  	st_input_bias_internal() = 0.0;
  	st_previous_prediction_internal() = 0.0;
  	st_previous_applied_internal() = 0.0;
  	st_previous_valid_internal() = false;
  }
  if(st_trip_latched_internal()) {
  	st_COMMAND_ENABLE() = false;
  	st_COMMAND_DAC() = 0.0;
  	st_SELECTED_TARGET_DAC() = 0.0;
  	st_TRIPPED() = true;
  	st_TRIP_CODE() = st_trip_code_internal();
  	st_INPUT_BIAS_ESTIMATE_DAC() = st_input_bias_internal();
  	st_PREDICTED_MAX_RAW() = -1.0;
  	st_PREDICTED_FINAL_RAW() = -1.0;
  }
  else if((! st_ENABLE_REQUEST())) {
  	st_input_bias_internal() = 0.0;
  	st_previous_prediction_internal() = 0.0;
  	st_previous_applied_internal() = 0.0;
  	st_previous_valid_internal() = false;
  	st_COMMAND_ENABLE() = false;
  	st_COMMAND_DAC() = 0.0;
  	st_SELECTED_TARGET_DAC() = 0.0;
  	st_TRIPPED() = false;
  	st_TRIP_CODE() = 0;
  	st_INPUT_BIAS_ESTIMATE_DAC() = 0.0;
  	st_PREDICTED_MAX_RAW() = -1.0;
  	st_PREDICTED_FINAL_RAW() = -1.0;
  }
  else {
  	if((! st_EXTERNAL_HEALTHY())) {
  		st_trip_latched_internal() = true;
  		st_trip_code_internal() = 1;
  	}
  	else if((! ((((((st_PV_RAW() == st_PV_RAW()) && (st_PV_RAW() >= 0.0)) && (st_PV_RAW() < 1000000.0)) && (st_PV_MODEL() == st_PV_MODEL())) && (st_PV_MODEL() >= 0.0)) && (st_PV_MODEL() < 1000000.0)))) {
  		st_trip_latched_internal() = true;
  		st_trip_code_internal() = 2;
  	}
  	else if((st_PV_RAW() >= 800.0)) {
  		st_trip_latched_internal() = true;
  		st_trip_code_internal() = 3;
  	}
  	else if((! (((st_APPLIED_DAC() == st_APPLIED_DAC()) && (st_APPLIED_DAC() >= 0.0)) && (st_APPLIED_DAC() <= 12000.0)))) {
  		st_trip_latched_internal() = true;
  		st_trip_code_internal() = 4;
  	}
  	else if((! (((st_SP_RAW() == st_SP_RAW()) && (st_SP_RAW() >= 0.0)) && (st_SP_RAW() < 800.0)))) {
  		st_trip_latched_internal() = true;
  		st_trip_code_internal() = 5;
  	}
  	if(st_trip_latched_internal()) {
  		st_COMMAND_ENABLE() = false;
  		st_COMMAND_DAC() = 0.0;
  		st_SELECTED_TARGET_DAC() = 0.0;
  		st_TRIPPED() = true;
  		st_TRIP_CODE() = st_trip_code_internal();
  		st_INPUT_BIAS_ESTIMATE_DAC() = st_input_bias_internal();
  		st_PREDICTED_MAX_RAW() = -1.0;
  		st_PREDICTED_FINAL_RAW() = -1.0;
  	}
  	else {
  		if(st_previous_valid_internal()) {
  			st_residual() = SUB(st_PV_MODEL(), st_previous_prediction_internal());
  			st_effective_input() = SUB(ADD(st_previous_applied_internal(), st_input_bias_internal()), 11750.0);
  			if((st_effective_input() < 0.0)) {
  				st_effective_input() = 0.0;
  			}
  			else if((st_effective_input() > 500.0)) {
  				st_effective_input() = 500.0;
  			}
  			if((st_effective_input() <= 0.0)) {
  				st_phi_value() = 0.0;
  				st_phi_slope() = 0.0;
  			}
  			else if((st_effective_input() <= 50.0)) {
  				st_phi_value() = ADD(0.0, MUL(2.18672414788656, SUB(st_effective_input(), 0.0)));
  				st_phi_slope() = 2.18672414788656;
  			}
  			else if((st_effective_input() <= 100.0)) {
  				st_phi_value() = ADD(109.336207394328, MUL(2.8370487151326, SUB(st_effective_input(), 50.0)));
  				st_phi_slope() = 2.8370487151326;
  			}
  			else if((st_effective_input() <= 150.0)) {
  				st_phi_value() = ADD(251.188643150958, MUL(3.14843691926082, SUB(st_effective_input(), 100.0)));
  				st_phi_slope() = 3.14843691926082;
  			}
  			else if((st_effective_input() <= 200.0)) {
  				st_phi_value() = ADD(408.610489113999, MUL(3.36938946497773, SUB(st_effective_input(), 150.0)));
  				st_phi_slope() = 3.36938946497773;
  			}
  			else if((st_effective_input() <= 250.0)) {
  				st_phi_value() = ADD(577.079962362885, MUL(3.5438415941052, SUB(st_effective_input(), 200.0)));
  				st_phi_slope() = 3.5438415941052;
  			}
  			else if((st_effective_input() <= 300.0)) {
  				st_phi_value() = ADD(754.272042068145, MUL(3.68936702582848, SUB(st_effective_input(), 250.0)));
  				st_phi_slope() = 3.68936702582848;
  			}
  			else if((st_effective_input() <= 350.0)) {
  				st_phi_value() = ADD(938.740393359569, MUL(3.81495379764048, SUB(st_effective_input(), 300.0)));
  				st_phi_slope() = 3.81495379764048;
  			}
  			else if((st_effective_input() <= 400.0)) {
  				st_phi_value() = ADD(1129.48808324159, MUL(3.92587047388803, SUB(st_effective_input(), 350.0)));
  				st_phi_slope() = 3.92587047388803;
  			}
  			else if((st_effective_input() <= 450.0)) {
  				st_phi_value() = ADD(1325.78160693599, MUL(4.0254915737244, SUB(st_effective_input(), 400.0)));
  				st_phi_slope() = 4.0254915737244;
  			}
  			else if((st_effective_input() <= 500.0)) {
  				st_phi_value() = ADD(1527.05618562221, MUL(4.11611844531302, SUB(st_effective_input(), 450.0)));
  				st_phi_slope() = 4.11611844531302;
  			}
  			else {
  				st_phi_value() = 1732.86210788787;
  				st_phi_slope() = 4.11611844531302;
  			}
  			st_sensitivity() = MUL(0.00212320412289765, st_phi_slope());
  			if((st_sensitivity() > 1.0E-6)) {
  				st_bias_update() = DIV(MUL(0.01, st_residual()), st_sensitivity());
  				if((st_bias_update() > 5.0)) {
  					st_bias_update() = 5.0;
  				}
  				else if((st_bias_update() < -5.0)) {
  					st_bias_update() = -5.0;
  				}
  				st_input_bias_internal() = ADD(st_input_bias_internal(), st_bias_update());
  				if((st_input_bias_internal() > 250.0)) {
  					st_input_bias_internal() = 250.0;
  				}
  				else if((st_input_bias_internal() < -250.0)) {
  					st_input_bias_internal() = -250.0;
  				}
  			}
  		}
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
  					st_candidate_target() = 11540.6816771227;
  					break;
  				case 2:
  					st_candidate_target() = 11590.6816771227;
  					break;
  				case 3:
  					st_candidate_target() = 11640.6816771227;
  					break;
  				case 4:
  					st_candidate_target() = 11690.6816771227;
  					break;
  				case 5:
  					st_candidate_target() = 11740.6816771227;
  					break;
  				case 6:
  					st_candidate_target() = 11790.6816771227;
  					break;
  				case 7:
  					st_candidate_target() = 11840.6816771227;
  					break;
  				case 8:
  					st_candidate_target() = 11890.6816771227;
  					break;
  				case 9:
  					st_candidate_target() = 11940.6816771227;
  					break;
  				case 10:
  					st_candidate_target() = 11990.6816771227;
  					break;
  				case 11:
  					st_candidate_target() = 11750.0;
  					break;
  				case 12:
  					st_candidate_target() = 12000.0;
  					break;
  				default:
  					st_candidate_target() = 0.0;
  					break;
  			}
  			st_predicted_y() = st_PV_MODEL();
  			st_predicted_u() = st_APPLIED_DAC();
  			st_previous_u() = st_APPLIED_DAC();
  			st_candidate_cost() = 0.0;
  			st_candidate_predicted_max() = st_predicted_y();
  			st_candidate_feasible() = true;
  			const auto by_0 = 1;
  			const auto to_0 = 200;
  			for(st_prediction_index() = 1;
  			    (by_0 >  0 && st_prediction_index() <= to_0) ||
  			    (by_0 <= 0 && st_prediction_index() >= to_0);
  			    st_prediction_index() = st_prediction_index() + by_0){
  				if(st_candidate_feasible()) {
  					st_delta_u() = SUB(st_candidate_target(), st_predicted_u());
  					if((st_delta_u() > 150.0)) {
  						st_delta_u() = 150.0;
  					}
  					else if((st_delta_u() < -150.0)) {
  						st_delta_u() = -150.0;
  					}
  					st_predicted_u() = ADD(st_predicted_u(), st_delta_u());
  					if((st_predicted_u() > 12000.0)) {
  						st_predicted_u() = 12000.0;
  					}
  					else if((st_predicted_u() < 0.0)) {
  						st_predicted_u() = 0.0;
  					}
  					st_effective_model_u() = ADD(st_predicted_u(), st_input_bias_internal());
  					if((st_effective_model_u() > 12250.0)) {
  						st_effective_model_u() = 12250.0;
  					}
  					else if((st_effective_model_u() < 0.0)) {
  						st_effective_model_u() = 0.0;
  					}
  					st_effective_input() = SUB(st_effective_model_u(), 11750.0);
  					if((st_effective_input() < 0.0)) {
  						st_effective_input() = 0.0;
  					}
  					else if((st_effective_input() > 500.0)) {
  						st_effective_input() = 500.0;
  					}
  					if((st_effective_input() <= 0.0)) {
  						st_phi_value() = 0.0;
  						st_phi_slope() = 0.0;
  					}
  					else if((st_effective_input() <= 50.0)) {
  						st_phi_value() = ADD(0.0, MUL(2.18672414788656, SUB(st_effective_input(), 0.0)));
  						st_phi_slope() = 2.18672414788656;
  					}
  					else if((st_effective_input() <= 100.0)) {
  						st_phi_value() = ADD(109.336207394328, MUL(2.8370487151326, SUB(st_effective_input(), 50.0)));
  						st_phi_slope() = 2.8370487151326;
  					}
  					else if((st_effective_input() <= 150.0)) {
  						st_phi_value() = ADD(251.188643150958, MUL(3.14843691926082, SUB(st_effective_input(), 100.0)));
  						st_phi_slope() = 3.14843691926082;
  					}
  					else if((st_effective_input() <= 200.0)) {
  						st_phi_value() = ADD(408.610489113999, MUL(3.36938946497773, SUB(st_effective_input(), 150.0)));
  						st_phi_slope() = 3.36938946497773;
  					}
  					else if((st_effective_input() <= 250.0)) {
  						st_phi_value() = ADD(577.079962362885, MUL(3.5438415941052, SUB(st_effective_input(), 200.0)));
  						st_phi_slope() = 3.5438415941052;
  					}
  					else if((st_effective_input() <= 300.0)) {
  						st_phi_value() = ADD(754.272042068145, MUL(3.68936702582848, SUB(st_effective_input(), 250.0)));
  						st_phi_slope() = 3.68936702582848;
  					}
  					else if((st_effective_input() <= 350.0)) {
  						st_phi_value() = ADD(938.740393359569, MUL(3.81495379764048, SUB(st_effective_input(), 300.0)));
  						st_phi_slope() = 3.81495379764048;
  					}
  					else if((st_effective_input() <= 400.0)) {
  						st_phi_value() = ADD(1129.48808324159, MUL(3.92587047388803, SUB(st_effective_input(), 350.0)));
  						st_phi_slope() = 3.92587047388803;
  					}
  					else if((st_effective_input() <= 450.0)) {
  						st_phi_value() = ADD(1325.78160693599, MUL(4.0254915737244, SUB(st_effective_input(), 400.0)));
  						st_phi_slope() = 4.0254915737244;
  					}
  					else if((st_effective_input() <= 500.0)) {
  						st_phi_value() = ADD(1527.05618562221, MUL(4.11611844531302, SUB(st_effective_input(), 450.0)));
  						st_phi_slope() = 4.11611844531302;
  					}
  					else {
  						st_phi_value() = 1732.86210788787;
  						st_phi_slope() = 4.11611844531302;
  					}
  					st_predicted_y() = ADD(ADD(298.0, MUL(0.996879877730208, SUB(st_predicted_y(), 298.0))), MUL(0.00212320412289765, st_phi_value()));
  					if((st_predicted_y() > st_candidate_predicted_max())) {
  						st_candidate_predicted_max() = st_predicted_y();
  					}
  					if((! ((st_predicted_y() == st_predicted_y()) && (st_predicted_y() <= 750.0)))) {
  						st_candidate_feasible() = false;
  					}
  					else {
  						st_tracking_error() = SUB(st_predicted_y(), st_SP_RAW());
  						st_move_value() = SUB(st_predicted_u(), st_previous_u());
  						st_candidate_cost() = ADD(ADD(st_candidate_cost(), MUL(st_tracking_error(), st_tracking_error())), MUL(MUL(2.0E-4, st_move_value()), st_move_value()));
  						if((st_predicted_y() > 650.0)) {
  							st_soft_excess() = SUB(st_predicted_y(), 650.0);
  							st_candidate_cost() = ADD(st_candidate_cost(), MUL(MUL(20.0, st_soft_excess()), st_soft_excess()));
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
  			st_COMMAND_ENABLE() = false;
  			st_COMMAND_DAC() = 0.0;
  			st_SELECTED_TARGET_DAC() = 0.0;
  			st_TRIPPED() = true;
  			st_TRIP_CODE() = st_trip_code_internal();
  			st_INPUT_BIAS_ESTIMATE_DAC() = st_input_bias_internal();
  			st_PREDICTED_MAX_RAW() = -1.0;
  			st_PREDICTED_FINAL_RAW() = -1.0;
  		}
  		else {
  			st_delta_u() = SUB(st_best_target(), st_APPLIED_DAC());
  			if((st_delta_u() > 150.0)) {
  				st_delta_u() = 150.0;
  			}
  			else if((st_delta_u() < -150.0)) {
  				st_delta_u() = -150.0;
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
  			st_TRIPPED() = false;
  			st_TRIP_CODE() = 0;
  			st_INPUT_BIAS_ESTIMATE_DAC() = st_input_bias_internal();
  			st_PREDICTED_MAX_RAW() = st_best_predicted_max();
  			st_PREDICTED_FINAL_RAW() = st_best_predicted_final();
  			st_effective_model_u() = ADD(st_command_candidate(), st_input_bias_internal());
  			if((st_effective_model_u() > 12250.0)) {
  				st_effective_model_u() = 12250.0;
  			}
  			else if((st_effective_model_u() < 0.0)) {
  				st_effective_model_u() = 0.0;
  			}
  			st_effective_input() = SUB(st_effective_model_u(), 11750.0);
  			if((st_effective_input() < 0.0)) {
  				st_effective_input() = 0.0;
  			}
  			else if((st_effective_input() > 500.0)) {
  				st_effective_input() = 500.0;
  			}
  			if((st_effective_input() <= 0.0)) {
  				st_phi_value() = 0.0;
  				st_phi_slope() = 0.0;
  			}
  			else if((st_effective_input() <= 50.0)) {
  				st_phi_value() = ADD(0.0, MUL(2.18672414788656, SUB(st_effective_input(), 0.0)));
  				st_phi_slope() = 2.18672414788656;
  			}
  			else if((st_effective_input() <= 100.0)) {
  				st_phi_value() = ADD(109.336207394328, MUL(2.8370487151326, SUB(st_effective_input(), 50.0)));
  				st_phi_slope() = 2.8370487151326;
  			}
  			else if((st_effective_input() <= 150.0)) {
  				st_phi_value() = ADD(251.188643150958, MUL(3.14843691926082, SUB(st_effective_input(), 100.0)));
  				st_phi_slope() = 3.14843691926082;
  			}
  			else if((st_effective_input() <= 200.0)) {
  				st_phi_value() = ADD(408.610489113999, MUL(3.36938946497773, SUB(st_effective_input(), 150.0)));
  				st_phi_slope() = 3.36938946497773;
  			}
  			else if((st_effective_input() <= 250.0)) {
  				st_phi_value() = ADD(577.079962362885, MUL(3.5438415941052, SUB(st_effective_input(), 200.0)));
  				st_phi_slope() = 3.5438415941052;
  			}
  			else if((st_effective_input() <= 300.0)) {
  				st_phi_value() = ADD(754.272042068145, MUL(3.68936702582848, SUB(st_effective_input(), 250.0)));
  				st_phi_slope() = 3.68936702582848;
  			}
  			else if((st_effective_input() <= 350.0)) {
  				st_phi_value() = ADD(938.740393359569, MUL(3.81495379764048, SUB(st_effective_input(), 300.0)));
  				st_phi_slope() = 3.81495379764048;
  			}
  			else if((st_effective_input() <= 400.0)) {
  				st_phi_value() = ADD(1129.48808324159, MUL(3.92587047388803, SUB(st_effective_input(), 350.0)));
  				st_phi_slope() = 3.92587047388803;
  			}
  			else if((st_effective_input() <= 450.0)) {
  				st_phi_value() = ADD(1325.78160693599, MUL(4.0254915737244, SUB(st_effective_input(), 400.0)));
  				st_phi_slope() = 4.0254915737244;
  			}
  			else if((st_effective_input() <= 500.0)) {
  				st_phi_value() = ADD(1527.05618562221, MUL(4.11611844531302, SUB(st_effective_input(), 450.0)));
  				st_phi_slope() = 4.11611844531302;
  			}
  			else {
  				st_phi_value() = 1732.86210788787;
  				st_phi_slope() = 4.11611844531302;
  			}
  			st_previous_prediction_internal() = ADD(ADD(298.0, MUL(0.996879877730208, SUB(st_PV_MODEL(), 298.0))), MUL(0.00212320412289765, st_phi_value()));
  			st_previous_applied_internal() = st_command_candidate();
  			st_previous_valid_internal() = true;
  		}
  	}
  }
}


void FORTE_MPC_MOVE_BLOCKED_NMPC_V1::enterStateSTART(void) {
  m_nECCState = scm_nStateSTART;
}

void FORTE_MPC_MOVE_BLOCKED_NMPC_V1::enterStateEXEC(void) {
  m_nECCState = scm_nStateEXEC;
  alg_ALG_NMPC();
  sendOutputEvent(scm_nEventCNFID);
}


void FORTE_MPC_MOVE_BLOCKED_NMPC_V1::executeEvent(int pa_nEIID){
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


