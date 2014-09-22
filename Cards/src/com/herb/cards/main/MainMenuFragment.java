package com.herb.cards.main;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainMenuFragment extends Fragment implements OnClickListener
{
	public interface Listener
	{
		public abstract void openGame(String gameId, int status);
		public abstract void setTitle(String title);
		public abstract void goToCreateGameScreen();
		public abstract void goToPendingGameListScreen();
	}
	
	private Listener listener;
	
	private static int[] CLICKABLES = {R.id.go_to_create_game_text_view, R.id.go_to_pending_games_text_view};
	
	private static final int NO_ALERTS = 0;
	private static final int GAME_ALERT = 1;
	
	private String[] gameIds = {};
	private String[] gameNames = {};
	private int[] gameStatuses = {};
	private int[] gameAlerts = {};
	
	private TextView[] gameTextViews = {};
	
	private LinearLayout activeGameLinearLayout, waitingGameLinearLayout;
	
	@Override
	public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState)
	{
		View v = inflater.inflate(R.layout.fragment_main_menu_screen, container, false);
		
		for(int i : CLICKABLES)
			v.findViewById(i).setOnClickListener(this);
			
		activeGameLinearLayout = (LinearLayout) v.findViewById(R.id.active_game_list_linear_layout);
		waitingGameLinearLayout = (LinearLayout) v.findViewById(R.id.waiting_game_list_linear_layout);
		return v;
	}

	@Override
	public void onStart()
	{
		super.onStart();
		updateUi();
	}
	
	@Override
	public void onClick(View v)
	{
			
		switch(v.getId())
		{
			case R.id.go_to_create_game_text_view:
				listener.goToCreateGameScreen();
				break;
			case R.id.go_to_pending_games_text_view:
				listener.goToPendingGameListScreen();
				break;
			default:
				for(int i=0;i<gameTextViews.length;i++)
				{
					if(v.getTag().toString().equals(gameIds[i]))
						listener.openGame(gameIds[i], gameStatuses[i]);
				}
				break;
		}
	}

	public void setListener(Listener listener)
	{
		this.listener = listener;
	}
	
	public void setGames(JSONArray gameList)
	{
		int length = gameList.length();
		gameIds = new String[length];
		gameNames = new String[length];
		gameStatuses = new int[length];
		gameAlerts = new int[length];
		
		for(int i=0;i<length;i++)
		{
			try
			{
				JSONObject game = gameList.getJSONObject(i);
				
				gameIds[i] = game.getString("gameId");
				gameNames[i] = game.getString("gameName");
				gameStatuses[i] = game.getInt("gameStatus");
				gameAlerts[i] = game.getInt("alert");
			} catch (JSONException e)
			{
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
	}
	
	public void updateUi()
	{
		if(getActivity() == null)
			return;
		
		if(listener == null)
			return;
		
		listener.setTitle("My Games");
		
		activeGameLinearLayout.removeAllViews();
		waitingGameLinearLayout.removeAllViews();
		
		gameTextViews = new TextView[gameIds.length];
		
		for(int i=0;i<gameIds.length;i++)
		{
			TextView gameTextView = new TextView(getActivity());
			gameTextView.setTag(gameIds[i]);
			
			gameTextView.setText(gameNames[i]);
			gameTextView.setClickable(true);
			gameTextView.setOnClickListener(this);
			gameTextView.setBackground(getResources().getDrawable(R.drawable.white_card));
			gameTextView.setTextAppearance(getActivity(), R.style.WhiteCard);
			
			if(gameAlerts[i] == GAME_ALERT)
				activeGameLinearLayout.addView(gameTextView);
			else if(gameAlerts[i] == NO_ALERTS)
				waitingGameLinearLayout.addView(gameTextView);
			gameTextViews[i] = gameTextView;
		}
		
		if(activeGameLinearLayout.getChildCount() == 0)
		{
			TextView emptyTextView = new TextView(getActivity());
			emptyTextView.setText("No Games");
			emptyTextView.setBackground(getResources().getDrawable(R.drawable.white_card));
			emptyTextView.setTextAppearance(getActivity(), R.style.WhiteCard);
			activeGameLinearLayout.addView(emptyTextView);
		}
		if(waitingGameLinearLayout.getChildCount() == 0)
		{
			TextView emptyTextView = new TextView(getActivity());
			emptyTextView.setText("No Games");
			emptyTextView.setBackground(getResources().getDrawable(R.drawable.white_card));
			emptyTextView.setTextAppearance(getActivity(), R.style.WhiteCard);
			waitingGameLinearLayout.addView(emptyTextView);
		}
	}
}
